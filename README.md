# 🕊️ Eirene-v1

`Eirene-v1` is an AI-based counseling chatbot designed to support the self-determination of Korean terminal cancer patients.

It employs a multi-agent architecture to address complex counseling needs and incorporates a dual-memory system consisting of short-term and long-term memory. The backend is built with FastAPI, and a SvelteKit-based interface is provided for testing.

\* The currently released code corresponds to the initial prototype (v1). To avoid influencing subsequent development, detailed components such as data and prompt designs are not disclosed.

In later versions,

- v2: the counseling stages were redesigned to better align with clinical settings.
- v3: the system components were reconfigured through ablation studies.

![Architecture](/assets/architecture.png)

## 🐋 Run

```sh
$ git clone git@github.com:denev6/eirene-v1.git
$ cd eirene-v1
$ docker compose up --build
```

The API documentation is provided in [chat/README.md](/chat).

## 🔗 Citation

### v1

```bib
@article{ART003300255,
  author  = {Sung-Jin Park and Huilin Piao and Seo-In Choi and Ha-Young Oh},
  title   = {A Multi-Agent System for End-of-Life Decision Support in Terminal Cancer Care},
  journal = {Journal of the Korea Institute of Information and Communication Engineering},
  year    = {2026},
  volume  = {30},
  number  = {1},
  pages   = {179--186},
  issn    = {2234-4772}
}
```

Dev Log: [임종 결정 지원을 위한 AI 챗봇 개발기](https://denev6.github.io/posts/eirene)

### v3

```bib
@article{🔥forthcoming,
  author  = {Sung-Jin Park and Huilin Piao and Seo-In Choi and Jun-Bo Shim and Ha-Young Oh},
  title   = {Constraint Optimization Modeling for End-of-Life Counseling Using Multi-Agent Systems},
  journal = {Journal of the Korea Institute of Information and Communication Engineering},
  year    = {2026},
  volume  = {30},
  number  = {2}
}
```
