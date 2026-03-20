---
layout: ontology_detail
id: clco
title: Clinical Context Ontology
jobs:
  - id: https://travis-ci.org/ozborn/clinreason
    type: travis-ci
build:
  checkout: git clone https://github.com/ozborn/clinreason.git
  system: git
  path: "."
contact:
  email: ozborn@uab.edu
  label: John Osborne
  github: ozborn
description: Open ontology for tracking the clinical context of a patient including treatment rationale, diagnostic reasoning and issues related to care context.
domain: clinical
homepage: https://github.com/ozborn/clinreason
products:
  - id: clco.owl
    name: "Clinical Context Ontology main release in OWL format"
  - id: clco.obo
    name: "Clinical Context Ontology additional release in OBO format"
  - id: clco.json
    name: "Clinical Context Ontology additional release in OBOJSon format"
  - id: clco/clco-base.owl
    name: "Clinical Context Ontology main release in OWL format"
  - id: clco/clco-base.obo
    name: "Clinical Context Ontology additional release in OBO format"
  - id: clco/clco-base.json
    name: "Clinical Context Ontology additional release in OBOJSon format"
dependencies:
- id: bfo

tracker: https://github.com/ozborn/clinreason/issues
license:
  url: http://creativecommons.org/licenses/by/4.0/
  label: CC-BY 4.0
activity_status: active
---

The Clinical Context Ontology (CLCO) captures clinical context around a patient's care, including the clinician's interpretations and decisions which are not well represented in the problem-focused EHR or other ontologies such as SNOMED CT. It covers treatment rationale, diagnostic reasoning, and issues related to care context. For more details, see [the publication](https://academic.oup.com/jamia/article/27/11/1648/5906104).

