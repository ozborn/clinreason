
![Build Status](https://github.com/ozborn/clinreason/workflows/CI/badge.svg)
# Clinical Context Ontology

Description: Open ontology for tracking the clinical context of a patient including treatment rationale, diagnostic reasoning and issues related to care context. The goal is to capture clinical context around a patient's care, including the clinician’s interpretations and decisions which are not well represented in the problem focused EHR or other ontologies such as SNOMED CT. For more details, see [the publication ](https://academic.oup.com/jamia/article/27/11/1648/5906104)

## Use Cases
* Synthetic Data Generation
* Extract Clinical reasoning (could use available case studies for training)

This ontology is under active development with a planned submission to the OBO Foundry. All 45 association classes have complete subject/object restriction axioms and IAO:0000115 definitions. Examples are provided as IAO:0000112 annotations.

## Versions

### Stable release versions

After acceptance, the latest version of the ontology will be found at:

http://purl.obolibrary.org/obo/clco.owl

(note this will not show up until the request has been approved by obofoundry.org)

### Editors' version

Editors of this ontology should use the edit version, [src/ontology/clco-edit.owl](src/ontology/clco-edit.owl)

## Contact

**Primary contact:** John D. Osborne ([@ozborn](https://github.com/ozborn)), ozborn@uab.edu, [ORCID 0000-0002-0851-1150](https://orcid.org/0000-0002-0851-1150)

Please use this GitHub repository's [Issue tracker](https://github.com/ozborn/clinreason/issues) to request new terms/classes or report errors or specific concerns related to the ontology.

## Acknowledgements

This ontology repository was created using the [Ontology Development Kit (ODK)](https://github.com/INCATools/ontology-development-kit).
