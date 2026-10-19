# Design Decisions

## Motivation for Reification of Clinical Associations

CLCO models clinical relationships (e.g., "has finding", "is caused by", "is admitted") as **classes** (subtypes of `clinical_association`, CLCO\_0000057) rather than as direct OWL object properties. Each association instance connects its participants via `has_subject` and `has_object` slots, following the [W3C N-ary Relations pattern](https://www.w3.org/TR/swbp-n-aryRelations/). This section documents why that design was chosen over the standard OBO approach of modeling relations as object properties.

### 1. Qualifier attachment requires a reified anchor

Clinical assertions are rarely bare facts. A statement like "the patient has diabetes" almost always carries contextual metadata: it may be **negated** ("the patient does not have diabetes"), **uncertain** ("the patient may have diabetes"), **historical** ("the patient had diabetes"), or **intended** rather than actual ("plan to start insulin"). CLCO captures these as six orthogonal qualifier axes (negation, uncertainty, temporal frame, completion status, intention, recommendation) that can be freely combined on any association.

OWL object property assertions are bare triples with no mechanism to attach per-assertion metadata. Without reification, there is no node on which to hang a negation flag or a temporal frame value. Workarounds such as OWL annotation assertions on axioms, RDF reification, or named graphs are non-standard in the OBO ecosystem and poorly supported by OWL-DL reasoners and OBO tooling.

### 2. Clinical NLP annotation demands instance-level provenance

CLCO's primary application is annotation of clinical reasoning in clinical notes for AI training. Each annotation is an instance of an association class: a specific "has finding" linking a specific patient to a specific condition, with specific qualifier values, anchored to a specific document. Annotators create, review, and adjudicate these instances.

Direct object properties produce anonymous triples that cannot be individually identified, counted, queried, or versioned. The reified pattern gives each assertion a stable identity that annotation tools, inter-annotator agreement metrics, and downstream machine learning pipelines can reference.

### 3. Generic participant slots enable cross-association queries

In the reified design, `has_subject` and `has_object` are two generic properties reused across all 51 association classes. Each class applies its own local restrictions (e.g., `is_admitted` restricts subject to patient and object to setting, while `is_caused_by` restricts subject to finding and object to finding or intervention). This means a single SPARQL or DL query using `has_subject` can retrieve all associations where the subject is a clinician, regardless of association type.

Converting to 51 separate object properties would eliminate these shared slots. Each property would carry its own domain and range (which is logically correct, using `owl:unionOf` where needed), but queries like "find every assertion about this patient" would require enumerating all properties whose domain includes patient. In practice this means maintaining a property-group abstraction outside the ontology (e.g., a SPARQL property path over a manually curated list) to recover the query capability that two generic slots provide natively.

### 4. The association taxonomy captures meaningful ontological structure

CLCO's association classes form a four-level IS-A hierarchy: `clinical_association` branches into `clinical_administration`, `clinical_decision`, `clinical_explanation`, and `has_finding`, each with further specializations. This hierarchy supports subsumption reasoning (e.g., "is admitted" IS-A "clinical administration" IS-A "clinical association") and enables queries at any level of granularity.

OBO ontologies do not conventionally maintain rich taxonomies of object properties. Converting to properties would flatten this structure, losing the ability to reason over categories of clinical associations -- for instance, retrieving all administrative associations or all explanation associations as coherent groups.

### 5. Data generation requires instantiable association templates

CLCO's second target application is generating synthetic clinical data for information extraction. The restriction axioms on association classes (e.g., "`is_caused_by` requires subject: finding, object: finding or intervention") serve as templates that constrain which entity combinations are valid. An instance generator can enumerate association classes, read their subject/object/qualifier constraints, and produce valid clinical statement instances.

Direct object properties cannot be instantiated as templates. A property like `is_caused_by` with domain and range constraints defines a schema but provides no instantiable object that a generation pipeline can populate, qualify, and serialize as a training example.

## Qualifier Scope Is Carried by the Property, Not the Class

A qualifier has two independent dimensions: **which axis** it belongs to, and **what it scopes
over**. CLCO assigns one to the class hierarchy and the other to the property.

- **Class = the axis.** `association_qualifier` (CLCO\_0000067) has exactly six direct children,
  the six orthogonal axes named above: `negation`, `uncertainty`, `temporal_frame`,
  `completion_status`, `intention`, `recommended`.
- **Property = the scope.** `has_statement_qualifier` (CLCO\_0003000) attaches a qualifier to the
  whole association; `has_participant_qualifier` (CLCO\_0002100) attaches it to a single
  `has_subject` or `has_object` participant. Both are sub-properties of
  `has_association_qualifier` (CLCO\_0002000), which is used when scope is deliberately left open.

The definitions of `negation` and `uncertainty` already state that they apply at any scope, so the
same class must be reachable at more than one scope. That is only expressible if scope lives on the
property.

### Why not encode scope in the class hierarchy

CLCO previously also had `statement_qualifier` (CLCO\_0000068) and `predicate_qualifier`
(CLCO\_0000069) as classes under `association_qualifier`. Both were obsoleted on 2026-10-19:

1. **It cannot express the cross-product.** Six axes over three scopes is eighteen combinations.
   The hierarchy only ever had two scope classes, and the axes were split across them
   arbitrarily — `negation`, `uncertainty` and `temporal_frame` sat beside `statement_qualifier`
   rather than under it, so *statement-scoped negation had no class at all*. The property was
   already the only thing carrying scope.
2. **It constrained nothing.** Neither `has_statement_qualifier` nor `has_participant_qualifier`
   declared a range, so the class hierarchy was decorative: nothing prevented attaching
   `intention` to a single participant. Scope constraints are now asserted where a reasoner can
   check them — see below.
3. **Predicate scope is not annotatable.** In the reified pattern the association node is anchored
   on the predicate itself, so a qualifier scoped to the predicate lands on the same node as one
   scoped to the statement. All three contextual examples formerly under `predicate_qualifier`
   turned out to be ordinary `uncertainty`, `historical` and `negation`. A
   `has_predicate_qualifier` sub-property can be added if a genuine case is ever found.

### How this is enforced

| property | range | meaning |
| --- | --- | --- |
| `has_association_qualifier` (CLCO\_0002000) | `association_qualifier` | any axis, scope unspecified |
| `has_statement_qualifier` (CLCO\_0003000) | `association_qualifier` | any axis, scoped to the whole association |
| `has_participant_qualifier` (CLCO\_0002100) | `negation` or `uncertainty` | only the scope-polymorphic axes may scope to a participant |

The range on `has_participant_qualifier` is what preserves the one fact the old hierarchy was
gesturing at: `intention`, `recommended` and `completion_status` are statement-only, because they
modify an assertion rather than a participant. `temporal_frame` is excluded for now and may be
revisited — see its curation note.

### What this means for annotation

The annotator never selects a property name. They tag the qualifier span with its axis, then draw
one arc; **the arc's target determines the scope, and therefore the property.**

```
"Possible pneumonia was treated with antibiotics."

  [pneumonia]     clinical entity      = finding
  [antibiotics]   clinical entity      = intervention
  [treated with]  clinical association = has_intervention
                                         has_subject -> [pneumonia]
                                         has_object  -> [antibiotics]
  [Possible]      association qualifier = uncertainty

  arc from [Possible] -> [pneumonia]      ==> has_participant_qualifier
  arc from [Possible] -> [treated with]   ==> has_statement_qualifier
```

The two readings differ clinically. Attaching to `[pneumonia]` says the treatment happened but the
diagnosis is uncertain, which is what this sentence means. Attaching to `[treated with]` says the
treatment itself may not have happened — correct for "The patient was possibly treated with
antibiotics elsewhere", wrong here. One qualifier class, one arc, two scopes.

This keeps the annotation tagset at six axes plus their values, with no scope entries, and makes
scope a consequence of where the annotator points rather than a separate judgement they must
record.

## Placement of Clinical Entities Under BFO entity

CLCO organizes its three top-level class hierarchies under BFO/IAO as follows:

- `clinical_association` (CLCO\_0000057) — subClassOf `IAO:0000030` (information content entity)
- `association_qualifier` (CLCO\_0000067) — subClassOf `IAO:0000030` (information content entity)
- `clinical_entity` (CLCO\_0000100) — subClassOf `BFO:0000001` (entity)

The 13 clinical entity types (finding, intervention, patient, clinician, time, reason, course, value, setting, task, documentation, finding site, patient state) are all subclasses of `clinical_entity` and therefore sit directly under BFO's root `entity` class.

### Rationale for the current placement

The current design treats clinical entities as proxies for real-world things. A `patient` stands for an actual person, a `finding` for an actual clinical observation, an `intervention` for an actual procedure or treatment. Under BFO-realist semantics, these are different ontological categories — a patient is a material entity, a finding is a quality or disposition, an intervention is a process, time is a temporal region — but they share no single BFO parent below `entity`. Placing `clinical_entity` under `BFO:0000001` acknowledges this heterogeneity without making a false commitment to any more specific BFO category.

### Considerations for an alternative placement under information content entity

There is a case for reclassifying `clinical_entity` under `IAO:0000030` (information content entity) alongside `clinical_association` and `association_qualifier`:

1. **Consistency within CLCO.** Two of the three CLCO pillars are already information content entities. Clinical entities fill the subject and object slots of those information structures. Placing them under a different BFO branch creates an asymmetry: the container is an information entity but its contents are not.

2. **What CLCO actually models.** CLCO's clinical entity types do not model real patients, real diseases, or real drugs. They model the *types of things mentioned in clinical text* that fill slots in reified associations. When an annotator tags "diabetes" in a note, they create a reference to a concept, not an instance of the disease itself. The definition of `clinical_entity` reflects this: "A core clinical entity over which all clinical context associations occur."

3. **Avoiding impossible BFO commitments.** Properly aligning each entity type under its correct BFO category (patient under material entity, finding under quality, intervention under process, time under temporal region) would prevent them from sharing a common CLCO parent class, since those BFO categories are disjoint. The only BFO class broad enough to serve as a shared parent for all 13 types is `entity` itself — which conveys no more information than `owl:Thing`.

4. **Alignment with CLCO's use cases.** Both primary applications (NLP annotation and clinical data generation) operate at the information level. Annotators mark up text mentions; generators produce structured data. Neither application requires a commitment to BFO-realist typing of the entities themselves — downstream systems use SNOMED CT, RxNorm, or LOINC codes for that purpose.

However, there are also reasons for caution:

- **BFO-realist expectations.** OBO reviewers accustomed to BFO-realist ontologies may find it unintuitive that a `patient` or `clinician` is classified as an information content entity. IAO:0000030 is defined as "a generically dependent continuant that is *about* some entity" — a patient is not *about* something. The counter-argument is that CLCO's `patient` class represents the concept-as-used-in-documentation, not an actual person.

- **Scope clarity.** Classifying entities as ICEs makes CLCO unambiguously an information ontology rather than a domain ontology. This is accurate for its stated purpose but may limit reuse by projects that want to bridge CLCO associations to real-world clinical data models.

### Status

This decision will be reviewed at a later date. The current placement under `BFO:0000001` is functional and does not cause validation or reasoning issues. A reclassification to `IAO:0000030` would be a one-line change (`CLCO_0000100 subClassOf IAO:0000030` instead of `BFO:0000001`) with no impact on restriction axioms or property declarations, but it carries implications for how the ontology positions itself relative to other OBO ontologies and should be made in consultation with OBO reviewers.
