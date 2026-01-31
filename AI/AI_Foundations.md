# 📘 OCI AI Foundations – Beginner-Friendly Notes

> These notes summarize my understanding and key learnings from the **OCI AI Foundations** course.

---

## 🤖 What is AI?

Artificial Intelligence (AI) is the ability of machines to imitate human intelligence, including cognitive abilities and problem-solving skills.

- **Artificial General Intelligence (AGI):** Can replicate human intelligence capabilities, such as learning new skills, thinking abstractly, and communicating. Applying AGI to solve problems in machines is what we generally refer to as AI.

**Why do we need AI?**
- Automation and decision-making
- Creative support

**AI Domains and Examples:**
- Language: Translation
- Vision: Image classification
- Speech: Text-to-speech
- Product recommendations: Cross-selling
- Anomaly detection: Fraudulent transaction detection
- Reinforcement learning: Self-driving cars
- Forecasting: Weather predictions
- Generating content: Images from text, etc.

---

## 🌐 AI vs ML vs DL

**Definitions:**
- **AI:** Broad field of making machines intelligent.
- **ML:** Subset of AI where systems learn from data.
- **DL:** Subset of ML using neural networks with multiple layers and predicts outcomes or generate new data.

**ML Categories:**
- **Supervised Learning:** Labeled data. Regression (output label - continuous), Classification (output label - categorical)
- **Unsupervised Learning:** Unlabeled data. Clustering (group similar items)
- **Reinforcement Learning:** Trial-and-error learning with agent–environment–reward setup

---

## 🧠 Neural Networks (ANN)

**Components:** Input, hidden, output layers; neurons(computational unit); weights(strength of connection between neurons); bias(additional input to neuron that allows certain degree of flexibility); activation functions(weighted sum of inputs to a neuron and produce output)

**Training (Backpropagation):**
1. Make a prediction
2. Compare with target → compute error
3. Adjust weights
4. Repeat over many examples

**Advantages:** Feature extraction, parallel processing, scalability, better performance

**Brief History:**
- 1950s: Artificial neurons, perceptron, MLP(multi-layer perceptron)
- 1990s: CNNs
- 2010: GPUs speed training
- 2012: AlexNet, DQN
- 2016: GANs(Generative Adversarial Networks), Transformers
- Today: LLMs, Diffusion Models

---

## 🧩 RNNs, LSTMs, CNNs

RNN - handles sequential data, maintains hidden state or memory, allow information to persist using feedback loop, capture dependencies

**RNN Sequence Mapping Types:**

- One-to-One: Single input → single output (e.g., image → label)
- One-to-Many: Single input → sequence (e.g., image → caption)
- Many-to-One: Sequence → single output (e.g., text → sentiment)
- Many-to-Many: Sequence → sequence (e.g., translation, NER)

**CNN:** Input → Convolution + activation → Pooling → Fully connected → Output
- Applications: Image classification, segmentation, face recognition, medical imaging, autonomous vehicles
- Limitations: Overfitting(working with limited training data), sensitivity, high computation(requires massive data and calculations), interpretability issues(similar to black box model)

**LSTM:** Selectively remembers or forgets information via gates; handles long-range dependencies and mitigates vanishing gradients problem. 

**Working of LSTM:**

Input processing(current data) → Previous Memory (previous hidden state values) → Gating Mechanism (core of lstm with input, forget and output gate) → Updating Memory (updates cell state by using info from input and forget gate) → Output Generation

---

## 🎨 Generative AI

- Creates new data following training data patterns
- Difference from ML: ML predicts known outputs; GenAI generates new content
- Types: Text-based, multimodal (text, images, audio, video)
- Applications: Content generation, medical imaging, NLP, creative tasks

**How GenAI different from other AI applications?:**

1. Data with labels -> ML model -> output -> label (appns - classfication, regression, recommdention systems)
2. Unstructerd data-> GenAI model -> output -> new content (appns -  text generations, image generations, videio generation)

---

## 📚 LLMs and Transformers

**LLM:** Probabilistic model of text sequences; predicts likely next words
- Example: “I am going to a birthday party. I took a ___ with me.” → likely “gift”

**Transformers:** Process tokens in parallel, model long-range dependencies via self-attention
- Encoder builds contextual representations
- Decoder generates outputs with cross-attention

---

## ✍️ Prompt Engineering

- Refine input prompts to elicit desired outputs
- Types: In-context, k-shot, chain-of-thought
- Mitigation of hallucinations: RAG, verification, constraints

---

## ⚙️ Customizing LLMs

- **Prompt Engineering:** Optimize inputs
- **RAG:** Augment model with external knowledge without modifying model
- **Fine-Tuning:** Adapt pre-trained models with custom datasets
- **Inference:** Generate outputs using trained models

**Benefits:** Better performance, domain adaptation, efficiency


