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
over**. CLCO assigns the axis to the class hierarchy and the scope to the property.

```
CLASS     qualifier (CLCO:0000067)          PROPERTY  has_qualifier (CLCO:0002000)
            ├─ negation                                 ├─ has_association_qualifier (CLCO:0003000)
            ├─ uncertainty                              │    ├─ has_temporal_frame     (CLCO:0002603)
            ├─ temporal_frame                           │    ├─ has_intention          (CLCO:0002002)
            │    └─ current / future /                  │    ├─ has_recommended        (CLCO:0002003)
            │       historical / hypothetical           │    └─ has_completion_status  (CLCO:0002604)
            ├─ completion_status                        ├─ has_subject_qualifier     (CLCO:0003001)
            │    └─ pending / in progress /             └─ has_object_qualifier      (CLCO:0003002)
            │       completed
            ├─ intention
            └─ recommended
```

| property | range | scopes |
| --- | --- | --- |
| `has_qualifier` | `qualifier` | nothing — grouping property, see below |
| `has_association_qualifier` | `qualifier` | the whole assertion |
| `has_subject_qualifier` | `negation` or `uncertainty` | the entity in the `has_subject` slot |
| `has_object_qualifier` | `negation` or `uncertainty` | the entity in the `has_object` slot |

`negation` and `uncertainty` apply at any scope, so the same class has to be reachable from more
than one property — which is only possible if scope lives on the property. The other four axes
modify an assertion rather than a participant, so they are statement-only; the ranges on the two
participant properties are what enforce that, and the four axis shorthands
(`has_temporal_frame`, `has_intention`, `has_recommended`, `has_completion_status`) sit under
`has_association_qualifier` because there is only one scope they could mean. `temporal_frame` may
become participant-scopeable later; see its curation note.

`has_qualifier` exists for querying, not annotation. Every scoped assertion entails it, so one
query retrieves qualifiers at any scope. The only legitimate direct use is data whose source did not
record scope.

### Why scope is not in the class hierarchy

1. **A class hierarchy cannot express the cross-product.** Six axes over three scopes is eighteen
   combinations. Any workable scope-as-class scheme has to either enumerate all eighteen or split
   the axes arbitrarily across scope classes, at which point some legitimate combinations have no
   class at all.
2. **Classes cannot constrain attachment.** The constraint that matters — `intention` may not scope
   a single participant — is a property range. Expressed as a class parent it is decorative; a
   reasoner cannot check it.
3. **Predicate scope is not annotatable.** In the reified pattern the association node is anchored
   on the predicate itself, so a qualifier scoped to the predicate lands on the same node as one
   scoped to the whole statement. The distinction cannot be drawn in an annotation tool, and every
   candidate example examined turned out to be ordinary `uncertainty`, `temporal_frame` or
   `negation`. A `has_predicate_qualifier` sub-property can be added if a genuine case appears.

### Why there is no statement tier

A `clinical_association` **is** the reified statement: a subclass of `IAO:0000030`, carrying its
participants through `has_subject` / `has_object`, with no separate `statement` class anywhere in
CLCO. "Statement scope" and "association scope" therefore denote the same node, and a property for
each would have identical domain and range. There is one property, `has_association_qualifier`.

### Why axis-only properties are avoided

A property naming the axis but not the scope — `has_negation_status`, say — discards the scope for
any axis that is scope-polymorphic, and makes the same annotation expressible several ways. Since
the axis is already carried by the value class, nothing is lost by requiring a scoped property. The
four axis shorthands that remain are unambiguous only because their axes are statement-only.

### Alignment with other models

- **SNOMED CT** *Situation with explicit context* attaches all six of its context attributes to the
  situation — the reified, contextualised assertion — with no intermediate tier. Its *Subject
  relationship context* identifies the participant role in the attribute name.
- **Biolink Model** has a `qualifier` grouping slot whose children encode scope in the slot name
  (`subject_*_qualifier`, `object_*_qualifier`), treats association-level qualifiers as the slots
  carrying no scope prefix, and has no `statement_qualifier` slot.

CLCO differs from Biolink in putting the axis in the value class rather than the slot name, which
trades a tailored range per axis for four properties instead of roughly nineteen slots. It also
differs on negation: Biolink's `negated` is a Boolean on `Association`, which cannot express
participant-scoped negation, whereas clinical text requires it ("Tenderness is present, but not in
the right upper quadrant"). That divergence is deliberate.

### Omission semantics (TENTATIVE — not yet settled)

> **Status: tentative.** The reading below is proposed, not decided. It is recorded because a
> consumer cannot interpret a missing triple without *some* convention, and leaving it unstated means
> every consumer invents its own. It should be confirmed or revised before the next release.

A missing triple does not mean the same thing everywhere in CLCO. Three readings are possible and
two of them are in use:

| slot kind | proposed reading of omission | examples |
| --- | --- | --- |
| qualifier axes | the **unmarked clinical default** | `negation` absent, `temporal frame` current |
| participant and value slots | genuinely **unspecified** | `finding site`, `has value`, `has duration` |
| *(not used in CLCO)* | **unrestricted / universal** | Biolink `species_context_qualifier` |

**Qualifier axes default to the unmarked reading.** Clinical documentation convention is that an
unmarked finding is affirmed, actual, about the patient, and current; only departures from that are
written down. This is the assumption behind ConText and NegEx, which flag deviations from
affirmed/recent/patient, and behind the distribution of the i2b2 assertion task, where *present* is
the majority class. SNOMED CT makes the same commitment explicitly by requiring default values for
Finding context, Temporal context and Subject relationship context.

**Participant and value slots are genuinely unspecified when absent.** "The patient has pain" with no
`finding site` does not mean pain at every site; it means the site was not recorded. Nothing should
be inferred.

**The third reading does not apply to CLCO.** A Biolink association is a claim about types in
general, so omitting a contextual qualifier leaves the claim unrestricted — which is why a
mouse-only finding can be misread as a human one. CLCO associations are particulars: one patient, one
document, one time. There is nothing to quantify over universally, so omission can never widen a
CLCO claim. Both models are open-world, but the risk runs in opposite directions: omission in Biolink
risks overclaiming, omission in CLCO risks underspecification.

**Consequence for the qualifier axes.** The two readings have to be distinguishable in the data,
because "affirmed because the annotator saw no negation cue" and "affirmed because nobody looked" are
not the same claim. OWL cannot express a defeasible default — it is monotonic and open-world, so
*not asserted* never entails *asserted not* — which means any default has to be either materialised
as data or left to the consuming layer. See the editors' guide for the mechanism; the ontology
itself only names the defaults.

### What this means for annotation

The annotator never selects a property name. They tag the qualifier span with its axis, then draw
one arc; **the arc's target determines the scope, and therefore the property.**

```
"Possible pneumonia was treated with antibiotics."

  [pneumonia]     clinical entity = finding
  [antibiotics]   clinical entity = intervention
  [treated with]  clinical association = has_intervention
                                         has_subject -> [pneumonia]
                                         has_object  -> [antibiotics]
  [Possible]      qualifier = uncertainty

  arc from [Possible] -> [pneumonia]      ==> has_subject_qualifier
  arc from [Possible] -> [antibiotics]    ==> has_object_qualifier
  arc from [Possible] -> [treated with]   ==> has_association_qualifier
```

The readings differ clinically. Attaching to `[pneumonia]` says the treatment happened but the
diagnosis is uncertain, which is what this sentence means. Attaching to `[treated with]` says the
treatment itself may not have happened — correct for "The patient was possibly treated with
antibiotics elsewhere", wrong here.

The annotation tagset stays at six axes plus their values, with no scope entries, and scope becomes
a consequence of where the annotator points rather than a separate judgement to record. Because the
arc already lands on a specific participant, the subject/object split is what lets the exported OWL
retain what the annotation captured.

## Placement of Clinical Entities Under BFO entity

CLCO's three top-level hierarchies sit as follows:

- `clinical_association` (CLCO\_0000057) — subClassOf `IAO:0000030` (information content entity)
- `qualifier` (CLCO\_0000067) — subClassOf `IAO:0000030` (information content entity)
- `clinical_entity` (CLCO\_0000100) — subClassOf `BFO:0000001` (entity)

The 14 clinical entity types (finding, intervention, patient, clinician, family member, time,
reason, course, value, setting, task, documentation, finding site, patient state) are all direct
subclasses of `clinical_entity`, and therefore sit directly under BFO's root `entity`.

### Rationale

Clinical entities are treated as proxies for real-world things: a `patient` stands for an actual
person, a `finding` for an actual observation, an `intervention` for an actual procedure. Under
BFO-realist semantics those are disjoint categories — material entity, quality or disposition,
process, temporal region — with no shared BFO parent below `entity`. Placing `clinical_entity`
under `BFO:0000001` acknowledges that heterogeneity without committing to a more specific category
that would be wrong for most of the 14.

### Open question: reclassification under information content entity

Unresolved, and recorded here because it affects how CLCO positions itself in OBO.

**For.** Two of the three CLCO pillars are already information content entities, and clinical
entities fill the subject and object slots of those structures, so the current split makes the
container an information entity while its contents are not. CLCO does not model real patients or
real diseases; it models the types of thing *mentioned in clinical text*, which is what
`clinical_entity`'s definition says — "A core clinical entity over which all clinical context
associations occur". Both use cases, annotation and data generation, operate at the information
level, and downstream systems use SNOMED CT, RxNorm or LOINC for real-world typing.

**Against.** `IAO:0000030` is defined as "a generically dependent continuant that is *about* some
entity", and a patient is not *about* anything, so OBO reviewers may find the classification
unintuitive. It would also mark CLCO unambiguously as an information ontology rather than a domain
ontology — accurate for its purpose, but possibly limiting for projects wanting to bridge CLCO
associations to real-world clinical data models.

The change itself is one line (`CLCO_0000100 subClassOf IAO:0000030`) with no effect on restriction
axioms or property declarations. The current placement is functional and raises no validation or
reasoning errors, so the decision should be made with OBO reviewers rather than unilaterally.
