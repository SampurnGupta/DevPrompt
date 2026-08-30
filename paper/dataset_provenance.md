# Dataset Provenance

Below is the academic-grade dataset provenance paragraph for the **Methodology** section of the DevPrompt paper:

```latex
\subsection{Dataset Provenance and Task Sampling}
To evaluate prompt formulation sensitivity under realistic conditions, we compiled a corpus of 1,264 developer task descriptions spanning seven distinct software engineering intents: \textit{debug}, \textit{generate}, \textit{refactor}, \textit{explain}, \textit{scaffold}, \textit{test}, and \textit{document}. These raw prompts represent unstructured developer requests, containing natural language disfluencies, informal programming terminology, and colloquial structural variations.

From this base corpus, we employed a stratified sampling approach to select a representative and computationally tractable evaluation set. First, developer requests were converted into dense vector representations using the $all-MiniLM-L6-v2$ sentence-transformer model. Within each intent class, $K$-Means clustering ($k=6$) was applied to partition the vector space. For each of the six clusters per class, the utterance nearest to the cluster centroid was sampled. To break ties and ensure representative task complexity, we selected the prompt exhibiting the highest entity richness, defined as the count of explicit references to programming languages, software frameworks, or error types. This yielded 42 highly diverse, centroid-adjacent tasks. We supplemented this set with 6 manually-authored composite tasks combining multiple intent classes (e.g., debug-and-test or refactor-and-document), resulting in a final evaluation dataset of 48 tasks.

\subsection{Ethics and Institutional Review}
Because the dataset consists entirely of anonymized, publicly available, and synthetically augmented developer requests containing no Personally Identifiable Information (PII) or proprietary corporate IP, this study does not involve human subjects research. Consequently, it is exempt from Institutional Review Board (IRB) review under standard institutional guidelines.
```
