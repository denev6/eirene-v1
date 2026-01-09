# National Cancer Knowledge Base

This document describes a curated cancer-related knowledge base derived from public resources provided by the U.S. National Cancer Institute (NCI), along with the vector database configuration used for semantic retrieval.

## Source and Copyright Policy

Unless otherwise indicated, all textual content originating from National Cancer Institute (NCI) materials is free of copyright and may be reused without prior permission. When reused, the NCI should be credited as the original source.

Reference:

* National Cancer Institute, *Reuse of Text Policy*: [https://www.cancer.gov/policies/copyright-reuse](https://www.cancer.gov/policies/copyright-reuse)

## Knowledge Scope (NCI Resources)

The knowledge base is constructed from the following NCI informational pages:

* **What Is Cancer**: [https://www.cancer.gov/about-cancer/understanding/what-is-cancer](https://www.cancer.gov/about-cancer/understanding/what-is-cancer)
* **Symptoms**: [https://www.cancer.gov/about-cancer/diagnosis-staging/symptoms](https://www.cancer.gov/about-cancer/diagnosis-staging/symptoms)
* **Common Types of Cancer**: [https://www.cancer.gov/types/common-cancers](https://www.cancer.gov/types/common-cancers)
* **Cancer Diagnosis**: [https://www.cancer.gov/about-cancer/diagnosis-staging/diagnosis](https://www.cancer.gov/about-cancer/diagnosis-staging/diagnosis)
* **Risk Factors**: [https://www.cancer.gov/about-cancer/causes-prevention/risk](https://www.cancer.gov/about-cancer/causes-prevention/risk)
* **Coping and Support**: [https://www.cancer.gov/about-cancer/coping](https://www.cancer.gov/about-cancer/coping)
* **Cancer Treatment**: [https://www.cancer.gov/about-cancer/treatment/types](https://www.cancer.gov/about-cancer/treatment/types)
* **Treatment Side Effects**: [https://www.cancer.gov/about-cancer/treatment/side-effects](https://www.cancer.gov/about-cancer/treatment/side-effects)

These resources cover foundational medical knowledge, patient-facing explanations, and supportive care information relevant to cancer prevention, diagnosis, treatment, and survivorship.

## Vector Database Configuration

* **Embedding Model**: `bge-m3`
* **Indexing / Search Method**: FAISS-based cosine similarity search

The vector database stores semantically embedded NCI-derived text segments and enables similarity-based retrieval to support tasks such as medical information lookup, question answering, and safety-constrained clinical dialogue systems.

## Intended Use

This knowledge base is designed to function as a factual and authoritative reference layer. It is suitable for integration into retrieval-augmented generation (RAG) pipelines, clinical decision support prototypes, and patient education systems where source transparency and content reliability are required.
