<template>
  <div id="app">
    <div class="sidebar" :class="{ 'sidebar-hidden': !isSidebarVisible }">
      <div class="sidebar-header">
        <h2>Team Paiya</h2>
        <button class="sidebar-toggle" @click="toggleSidebar" v-if="isMobile">
          {{ isSidebarVisible ? "✖" : "☰" }}
        </button>
      </div>

      <div class="usecase-grid">
        <div
          class="usecase-tile"
          v-for="(label, key) in useCases"
          :key="key"
          :class="{ active: useCase === key }"
          @click="selectUseCase(key)"
        >
          <span class="emoji">{{ label.icon }}</span>
          <span class="text">{{ label.name }}</span>
        </div>
      </div>

      <div class="tile-group">
        <div class="tile-label">🧠 Provider wählen:</div>
        <div class="tile-grid">
          <div
            v-for="p in Object.keys(availableModels)"
            :key="p"
            class="tile-button"
            :class="{ active: provider === p }"
            @click="provider = p"
          >
            {{ p.charAt(0).toUpperCase() + p.slice(1) }}
          </div>
        </div>
      </div>

      <div class="tile-group" v-if="availableModels[provider]">
        <div class="tile-label">🎯 Modell wählen:</div>
        <div class="tile-scroll-list">
          <div
            v-for="m in availableModels[provider]"
            :key="m"
            class="tile-button"
            :class="{ active: model === m }"
            @click="model = m"
          >
            {{ m }}
          </div>
        </div>
      </div>

      <p style="margin-top: 1rem; font-size: 0.85rem">
        Aktives Modell: <strong>{{ model }}</strong>
      </p>
    </div>

    <div class="main">
      <div v-if="quizWarning" class="quiz-warning-banner">
        ❗ {{ quizWarningMessage }}
      </div>
      <transition name="popup">
        <div v-if="showQuizResultPopup" class="quiz-result-popup">
          <p>
            🎉 Du hast {{ correctAnswers }}/10 Fragen richtig beantwortet ({{
              correctPercentage
            }}%)
          </p>
          <button @click="closeQuizResult">Weiter</button>
          <button @click="backToMenu" style="margin-left: 0.5rem;">
            Zurück zum Menü
          </button>
        </div>
      </transition>

      <div v-if="showInfoModal" class="usecase-info-modal">
        <h3>{{ useCases[useCase]?.name }}</h3>
        <p>{{ infoTexts[useCase] }}</p>
        <button @click="acknowledgeInfo">Got it!</button>
      </div>

      <div class="header">
        <h3>Willkommen bei paiya.ai</h3>
        <p>Mit Paiya.ia hast du deinen Assistenten immer an deiner Seite.</p>
      </div>
      <div v-if="!useCase" class="central-usecases">
        <h3>Wähle einen Anwendungsfall</h3>
        <div class="central-usecase-grid">
          <div
            v-for="(label, key) in useCases"
            :key="key"
            class="central-usecase-tile"
            @click="selectUseCase(key)"
          >
            <div class="icon">{{ label.icon }}</div>
            <div class="name">{{ label.name }}</div>
            <div class="description">
              <template v-if="key === 'Summary'"
                >Fasse Texte schnell und präzise zusammen.</template
              >
              <template v-else-if="key === 'Quiz'"
                >Erstelle ein Quiz zu deinem Wunschthema.</template
              >
              <template v-else-if="key === 'FreePrompt'"
                >Stelle beliebige Fragen oder gib Prompts ein.</template
              >
              <template v-else-if="key === 'FunFact'"
                >Erhalte interessante Fakten mit Quellenangabe.</template
              >
            </div>
          </div>
        </div>
      </div>

      <div class="chatbox">
        <div class="chat">
          <transition-group name="quiz" tag="div">
            <div
              v-for="(entry, index) in messages.filter(
                (e) => e.type !== 'hidden',
              )"
              :key="entry.type === 'quiz' ? `quiz-${index}` : `msg-${index}`"
            >
              <div
                v-if="entry.type !== 'quiz'"
                class="chat-entry"
                :class="{ 'chat-entry-user': entry.sender === 'user', 'chat-entry-bot': entry.sender === 'bot' }"
              >
                <div class="avatar" v-if="entry.sender === 'bot'">
                  <img
                    :src="botAvatar"
                    alt="Bot"
                    class="avatar-img"
                  />
                </div>

                <div class="message-content">
                  <div class="bubble">
                    <template v-if="typeof entry.text === 'string'">
                      <div v-html="renderMarkdown(entry.text)"></div>
                    </template>
                    <template v-else>
                      <div v-html="renderMarkdown(entry.text.text)"></div>
                      <div class="source">
                        Quelle:
                        <a
                          :href="entry.text.source"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {{ entry.text.source }}
                        </a>
                      </div>
                    </template>
                    <div class="timestamp">
                      {{ new Date(entry.timestamp).toLocaleTimeString() }}
                    </div>
                  </div>

                  <div class="rating-below" v-if="entry.sender === 'bot'">
                    <button
                      class="thumb-button"
                      :class="{ selected: chatRatings[index] === 'up' }"
                      @click="rateMessage(index, 'up')"
                      title="Gefällt mir"
                      :disabled="!!chatRatings[index]"
                    >
                      <svg
                        class="thumb-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path
                          d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
                        ></path>
                      </svg>
                    </button>
                    <button
                      class="thumb-button"
                      :class="{ selected: chatRatings[index] === 'down' }"
                      @click="rateMessage(index, 'down')"
                      title="Gefällt mir nicht"
                      :disabled="!!chatRatings[index]"
                    >
                      <svg
                        class="thumb-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      >
                        <path
                          d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7L2.34 12.7a2 2 0 0 0 2 2.3H7zM17 2h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"
                        ></path>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div v-else class="quiz-box">
                <div class="quiz-progress">
                  Frage {{ messages.filter(m => m.type === 'quiz').indexOf(entry) + 1 }} von 10
                </div>
                <h3>{{ entry.quiz.question }}</h3>
                <transition-group name="option" tag="ul">
                  <li
                    v-for="(opt, i) in entry.quiz.options"
                    :key="`option-${i}`"
                    :class="{ 'selected': entry.quiz.selected === opt }"
                  >
                    <button
                      @click="checkAnswer(entry.quiz, opt)"
                      :disabled="entry.quiz.selected !== null"
                      :class="{ 'correct': entry.quiz.selected === opt && opt === entry.quiz.answer, 'incorrect': entry.quiz.selected === opt && opt !== entry.quiz.answer }"
                    >
                      {{ opt }}
                    </button>
                  </li>
                </transition-group>
                <transition name="feedback">
                  <p v-if="entry.quiz.selected !== null" class="feedback">
                    <strong>
                      {{
                        entry.quiz.selected === entry.quiz.answer
                          ? "✅ Richtig!"
                          : "❌ Falsch. Richtige Antwort: " + entry.quiz.answer
                      }}
                    </strong>
                  </p>
                </transition>
                <transition name="feedback">
                  <p
                    v-if="entry.quiz.selected !== null && entry.quiz.explanation"
                    class="explanation"
                  >
                    💡 <em>{{ entry.quiz.explanation }}</em>
                  </p>
                </transition>
              </div>
            </div>
          </transition-group>
        </div>

        <div class="controls">
          <select v-if="useCase === 'Summary'" v-model="length">
            <option disabled value="">Zusammenfassungslänge wählen</option>
            <option>kurz</option>
            <option>mittel</option>
            <option>lang</option>
          </select>

          <div class="chat-input-wrapper">
            <input
              v-model="query"
              type="text"
              class="chat-input"
              :placeholder="
                useCase === 'Quiz'
                  ? 'Thema für das Quiz eingeben (z.B. Französischer Käse)'
                  : 'Stelle eine Frage oder gib einen Prompt ein'
              "
              :disabled="!useCase || isChatLocked || (useCase === 'Quiz' && isQuizInputLocked)"
              @keyup.enter.exact="handleEnter"
            />
            <button
              class="chat-send-button"
              @click="sendQuery"
              :disabled="!useCase || isChatLocked || (useCase === 'Quiz' && isQuizInputLocked)"
            >
              ➤
            </button>
          </div>

          <div v-if="useCase === 'Quiz' && quizStarted" class="quiz-controls">
            <button @click="cancelSession" class="cancel-button">
              Session abbrechen
            </button>
            <button @click="backToMenu" class="menu-button">
              Zurück zum Menü
            </button>
          </div>

          <div v-if="useCase && !quizStarted" class="menu-controls">
            <button @click="backToMenu" class="menu-button">
              Zurück zum Menü
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { marked } from "marked";
import DOMPurify from "dompurify";

marked.setOptions({
  breaks: true,
  gfm: true,
});

export default {
  data() {
    return {
      useCase: "",
      query: "",
      quizWarning: false,
      quizWarningMessage: "",
      length: "",
      provider: "groq",
      model: "gemma2-9b-it",
      messages: [],
      chatRatings: {},
      quizResults: [],
      showQuizResultPopup: false,
      quizStarted: false,
      isQuizInputLocked: false,
      isSidebarVisible: true,
      isMobile: false,
      infoAcknowledged: {
        Summary: false,
        Quiz: false,
        FreePrompt: false,
        FunFact: false,
      },
      showInfoModal: false,
      infoTexts: {
        Summary:
          "Mit dieser Funktion kannst du beliebige Texte automatisch zusammenfassen lassen – in kurz, mittel oder lang.",
        Quiz: "Erstelle dein eigenes Quiz und teste dein Wissen mit 10 spannenden Fragen! Gib ein beliebiges Thema ein.",
        FreePrompt: "Chatte einfach mit paiya.ia!",
        FunFact:
          "Gib ein Thema ein und erhalte interessante Fakten mit Quellenangabe!",
      },
      availableModels: {
        openai: ["gpt-4o", "gpt-3.5-turbo"],
        groq: [
          "gemma2-9b-it",
          "compound-beta-mini",
          "qwen-qwq-32b",
          "deepseek-r1-distill-llama-70b",
          "llama-3.3-70b-versatile",
          "allam-2-7b",
          "llama-3.1-8b-instant",
          "llama-guard-3-8b",
          "llama3-70b-8192",
          "llama3-8b-8192",
          "meta-llama/llama-4-maverick-17b-128e-instruct",
          "meta-llama/llama-4-scout-17b-16e-instruct",
          "mistral-saba-24b",
        ],
        google: ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        mistral: [
          "mistral-small-latest",
          "pixtral-12b-2409",
          "open-mistral-nemo",
          "open-codestral-mamba",
        ],
      },
      useCases: {
        Summary: { name: "Zusammenfassung", icon: "📄" },
        Quiz: { name: "Quiz", icon: "🔍" },
        FreePrompt: { name: "Freies Prompten", icon: "💬" },
        FunFact: { name: "Fun Fact", icon: "✨" },
      },
      botAvatar: "https://cdn-icons-png.flaticon.com/512/4712/4712107.png",
      userAvatar: "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
      quizTopic: "",
    };
  },
  mounted() {
    this.checkMobile();
    window.addEventListener("resize", this.checkMobile);
  },
  beforeDestroy() {
    window.removeEventListener("resize", this.checkMobile);
  },
  watch: {
    provider(newProvider) {
      this.model = this.availableModels[newProvider][0];
    },
  },
  computed: {
    correctAnswers() {
      return this.quizResults.filter((r) => r).length;
    },
    correctPercentage() {
      return Math.round((this.correctAnswers / 10) * 100);
    },
    isChatLocked() {
      return this.useCase && !this.infoAcknowledged[this.useCase];
    },
  },
  methods: {
    getGreeting(caseName) {
      switch (caseName) {
        case "Summary":
          return "Moin! Ich bin Paiya.ai und helfe dir, Texte schnell zusammenzufassen. Gib mir einen Text und wähle die Länge (kurz, mittel, lang)!";
        case "Quiz":
          return "Moin! Ich bin Paiya.ai und erstelle dir ein spannendes Quiz. Gib ein Thema ein, und ich stelle dir 10 Fragen!";
        case "FreePrompt":
          return "Moin! Ich bin Paiya.ai, dein virtueller Assistent. Wie kann ich dir helfen?";
        case "FunFact":
          return "Moin! Ich bin Paiya.ai und liefere dir interessante Fakten. Gib ein Thema ein, und ich finde einen Fun Fact für dich!";
        default:
          return "Moin! Ich bin Paiya.ai. Wie kann ich dir helfen?";
      }
    },
    selectUseCase(caseName) {
      this.useCase = caseName;
      if (!this.infoAcknowledged[caseName]) {
        this.showInfoModal = true;
        return;
      }
      this.resetState();
      this.messages.push({
        sender: "bot",
        type: "text",
        text: this.getGreeting(caseName),
        timestamp: new Date(),
      });
      if (this.isMobile) {
        this.isSidebarVisible = false;
      }
    },
    resetState() {
      this.messages = [];
      this.query = "";
      this.length = "";
      this.chatRatings = {};
      this.quizResults = [];
      this.showQuizResultPopup = false;
      this.quizStarted = false;
      this.isQuizInputLocked = false;
      this.quizTopic = "";
    },
    acknowledgeInfo() {
      this.infoAcknowledged[this.useCase] = true;
      this.showInfoModal = false;
      this.resetState();
      this.messages.push({
        sender: "bot",
        type: "text",
        text: this.getGreeting(this.useCase),
        timestamp: new Date(),
      });
    },
    handleEnter() {
      if (!this.query || !this.useCase || (this.useCase === 'Quiz' && this.isQuizInputLocked)) return;
      this.sendQuery();
    },
    backToMenu() {
      this.useCase = "";
      this.resetState();
    },
    cancelSession() {
      this.quizStarted = false;
      this.isQuizInputLocked = false;
      this.quizResults = [];
      this.messages = [];
      this.query = "";
      this.quizTopic = "";
    },
    closeQuizResult() {
      this.showQuizResultPopup = false;
      this.cancelSession();
    },
    showQuizWarning(message) {
      this.quizWarning = true;
      this.quizWarningMessage = message;
      setTimeout(() => {
        this.quizWarning = false;
        this.quizWarningMessage = "";
      }, 2500);
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const chatBox = this.$el.querySelector(".chat");
        if (chatBox) {
          chatBox.scrollTo({
            top: chatBox.scrollHeight,
            behavior: "smooth",
          });
        }
      });
    },
    async sendQuery(isNextQuestion = false) {
      const queryToSend = isNextQuestion ? this.quizTopic : this.query;

      if (!queryToSend) {
        this.showQuizWarning("Bitte gib ein Thema oder eine Frage ein.");
        return;
      }

      if (this.useCase === "Quiz") {
        const lastQuiz = [...this.messages]
          .reverse()
          .find((m) => m.type === "quiz");
        if (lastQuiz && lastQuiz.quiz && lastQuiz.quiz.selected === null && !isNextQuestion) {
          this.showQuizWarning("Bitte beantworte zuerst die aktuelle Quizfrage.");
          return;
        }
        if (!this.quizStarted) {
          this.quizStarted = true;
          this.isQuizInputLocked = true;
          this.quizTopic = this.query;
          // Nur beim ersten Quiz-Start die Benutzereingabe anzeigen
          this.messages.push({
            sender: "user",
            type: "text",
            text: queryToSend,
            timestamp: new Date(),
          });
        }
      } else {
        // Für andere Modi die Benutzereingabe immer anzeigen
        this.messages.push({
          sender: "user",
          type: "text",
          text: queryToSend,
          timestamp: new Date(),
        });
      }

      try {
        const response = await fetch(
          "https://it-services-team-paiya-gcp.gen-ai.software/api/process_query",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              query: queryToSend,
              use_case: this.useCase,
              length: this.length || undefined,
              provider: this.provider,
              model: this.model,
              messages: this.getContextMessages().slice(-20),
            }),
          },
        );

        if (!response.ok) {
          throw new Error(`HTTP-Fehler: ${response.status}`);
        }

        const result = await response.json();
        console.log("API-Antwort:", result);

        if (result.error) {
          if (result.error.includes("rate limit")) {
            alert("Rate limit erreicht. Bitte versuche es in einer Minute erneut.");
          } else {
            this.messages.push({
              sender: "bot",
              type: "text",
              text: `Fehler: ${result.error}`,
              timestamp: new Date(),
            });
          }
          this.cancelSession();
          return;
        }

        if (result.type === "quiz") {
          const quizObj = {
            question: result.question,
            options: result.options,
            answer: result.answer,
            explanation: result.explanation || "",
            selected: null,
          };

          this.messages.push({
            sender: "bot",
            type: "quiz",
            quiz: quizObj,
          });

          this.messages.push({
            sender: "bot",
            type: "hidden",
            text: `Frage: ${quizObj.question}\nAntwortmöglichkeiten:\n${quizObj.options.join(
              "\n",
            )}\nRichtige Antwort: ${quizObj.answer}\nErklärung: ${
              quizObj.explanation
            }`,
          });
          console.log("Quizfrage hinzugefügt:", quizObj);
        } else {
          let botReply = "";

          if (result.type === "free_prompt") botReply = result.data;
          else if (result.type === "summary") botReply = result.summary;
          else if (result.type === "fun_fact") {
            botReply = {
              text: result.fact,
              source: result.source,
            };
          } else {
            botReply = result.message || "Etwas ist schiefgelaufen...";
          }

          this.messages.push({
            sender: "bot",
            type: "text",
            text: botReply,
            timestamp: new Date(),
          });
        }
      } catch (error) {
        console.error("Fehler beim API-Aufruf:", error);
        this.messages.push({
          sender: "bot",
          type: "text",
          text: `Fehler beim Abrufen der Daten: ${error.message}`,
          timestamp: new Date(),
        });
        this.cancelSession();
        return;
      }

      if (this.useCase === "Quiz") {
        if (this.messages.length > 20) {
          this.messages = this.messages.slice(this.messages.length - 20);
        }
      } else if (this.useCase !== "FreePrompt") {
        if (this.messages.length > 10) {
          this.messages = this.messages.slice(this.messages.length - 10);
        }
      }

      if (!isNextQuestion) {
        this.query = "";
      }
      this.scrollToBottom();
    },
    getContextMessages() {
      return this.messages
        .filter((m) => m.sender === "user" || m.sender === "bot")
        .map((m) => {
          let content = "";

          if (typeof m.text === "string") {
            content = m.text;
          } else if (m.text && typeof m.text.text === "string") {
            content = m.text.text;
          } else if (m.type === "quiz" && m.quiz) {
            content = `Frage: ${
              m.quiz.question
            }\nAntwortmöglichkeiten:\n${m.quiz.options?.join(
              "\n",
            )}\nRichtige Antwort: ${m.quiz.answer}\nErklärung: ${
              m.quiz.explanation || ""
            }`;
          }

          return {
            role: m.sender === "user" ? "user" : "assistant",
            content,
          };
        });
    },
    async checkAnswer(quiz, selectedOption) {
      if (quiz.selected !== null) return;

      quiz.selected = selectedOption;
      const isCorrect = selectedOption === quiz.answer;

      this.quizResults.push(isCorrect);

      if (this.quizResults.length >= 10) {
        this.showQuizResultPopup = true;
        this.isQuizInputLocked = false;
        this.quizStarted = false;
      } else {
        await this.sendQuery(true);
      }

      this.scrollToBottom();
    },
    rateMessage(index, value) {
      if (this.chatRatings[index]) return;

      this.chatRatings[index] = value;

      const payload = {
        thumbs: value,
        message_index: index,
        model: this.model,
        provider: this.provider,
        feedback: this.feedback || "",
        messages: this.getContextMessages().slice(-20),
      };

      fetch(
        "https://it-services-team-paiya-gcp.gen-ai.software/api/store_feedback",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      )
        .then((res) => res.json())
        .then((data) => {
          console.log("Feedback aktualisiert:", data);
        })
        .catch((err) => {
          console.error("Fehler beim Feedback-Update:", err);
        });
    },
    renderMarkdown(text) {
      return DOMPurify.sanitize(marked(text));
    },
    toggleSidebar() {
      this.isSidebarVisible = !this.isSidebarVisible;
    },
    checkMobile() {
      this.isMobile = window.innerWidth <= 828;
      if (this.isMobile) {
        this.isSidebarVisible = true;
      } else {
        this.isSidebarVisible = true;
      }
    },
  },
};
</script>

<style scoped>
* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: nowrap;
  overflow: hidden;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f3f3f3;
}

#app {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  -webkit-overflow-scrolling: touch;
}

.sidebar {
  width: clamp(260px, 22vw, 400px);
  background-color: #002c5f;
  color: white;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  z-index: 1000;
  transition: transform 0.3s ease;
  -webkit-overflow-scrolling: touch;
}

.sidebar-hidden {
  transform: translateX(-100%);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-toggle {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #f0f4fa;
  height: 100vh;
  overflow: hidden;
  margin-left: clamp(260px, 22vw, 400px);
}

.header {
  flex-shrink: 0;
  padding: 1rem;
  background-color: #002c5f;
  color: white;
  border-bottom: 1px solid #ccc;
  position: fixed;
  top: 0;
  left: clamp(260px, 22vw, 400px);
  right: 0;
  z-index: 500;
  width: calc(100% - clamp(260px, 22vw, 400px));
}

.header h3 {
  font-size: clamp(1.2rem, 3.5vw, 1.5rem);
  margin: 0;
}

.header p {
  font-size: clamp(0.85rem, 2.5vw, 1rem);
  margin: 0.25rem 0 0;
}

.chatbox {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
  margin-top: 6rem;
  height: calc(100vh - 6rem);
}

.chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  overflow-y: auto;
  padding: 1rem;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

.chat-entry {
  display: flex;
  align-items: flex-start;
  width: 100%;
}

.chat-entry-bot {
  justify-content: flex-start;
}

.chat-entry-user {
  justify-content: flex-end;
  margin-bottom: 1rem;
}

.avatar {
  width: clamp(36px, 10vw, 40px);
  height: clamp(36px, 10vw, 40px);
  margin: 0 0.5rem;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #ccc;
}

.message-content {
  max-width: 70%;
}

.bubble {
  padding: 0.75rem;
  word-wrap: break-word;
  white-space: normal;
  text-align: justify;
  line-height: 1.5;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  position: relative;
}

.chat-entry-bot .bubble {
  background-color: #e0e9f7;
  color: #000;
  border-radius: 10px 10px 10px 0;
  margin-left: 0.5rem;
}

.chat-entry-user .bubble {
  background-color: #d1d1d1;
  color: #000;
  border-radius: 10px 0 10px 10px;
  margin-right: 0.5rem;
}

.source {
  font-size: clamp(0.75rem, 2vw, 0.85rem);
  color: #666;
  margin-top: 0.25rem;
  font-style: italic;
}

.source a {
  color: #004080;
  text-decoration: underline;
}

.timestamp {
  font-size: clamp(0.7rem, 2vw, 0.8rem);
  color: #888;
  margin-top: 0.25rem;
  text-align: right;
}

.controls {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background-color: #fff;
  position: sticky;
  bottom: 0;
  z-index: 500;
}

.controls input,
.controls select,
.controls button {
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  padding: 0.5rem;
  min-height: 44px;
}

.controls button {
  background-color: #002c5f;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  touch-action: manipulation;
}

.quiz-box {
  background-color: rgb(255, 243, 205);
  border: 1px solid rgb(255, 238, 186);
  padding: 1rem;
  margin-top: 1rem;
  border-radius: 10px;
  text-align: justify;
  max-width: 90%;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.quiz-progress {
  font-size: clamp(0.85rem, 2.5vw, 0.95rem);
  color: #555;
  margin-bottom: 0.5rem;
  text-align: center;
  font-weight: bold;
}

.quiz-box h3 {
  margin-bottom: 0.5rem;
  font-size: clamp(1.1rem, 3vw, 1.25rem);
}

.quiz-box ul {
  list-style-type: none;
  padding: 0;
}

.quiz-box li {
  margin-bottom: 0.5rem;
  transition: transform 0.2s ease;
}

.quiz-box li.selected button {
  transform: scale(1.05);
}

.quiz-box button {
  padding: 0.5rem 1rem;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  background-color: #004080;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  min-height: 44px;
  width: 100%;
  transition: background-color 0.2s, transform 0.2s;
}

.quiz-box button:hover:not(:disabled) {
  background-color: #0055aa;
  transform: scale(1.02);
}

.quiz-box button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.quiz-box button.correct {
  background-color: #28a745;
  animation: bounce 0.3s ease;
}

.quiz-box button.incorrect {
  background-color: #dc3545;
  animation: shake 0.3s ease;
}

.feedback {
  margin-top: 0.5rem;
  font-size: clamp(0.95rem, 2.5vw, 1rem);
  color: #004080;
}

.feedback strong {
  display: inline-block;
}

.explanation {
  margin-top: 0.5rem;
  font-size: clamp(0.85rem, 2.5vw, 0.95rem);
  color: #555;
  font-style: italic;
}

.usecase-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.usecase-tile {
  display: flex;
  align-items: center;
  background-color: #004080;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition:
    background-color 0.2s,
    transform 0.1s;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
}

.usecase-tile:hover {
  background-color: #0055aa;
  transform: translateY(-1px);
}

.usecase-tile.active {
  background-color: #003366;
  font-weight: bold;
  box-shadow: inset 0 0 0 2px white;
}

.usecase-tile .emoji {
  font-size: clamp(1.2rem, 4vw, 1.5rem);
  margin-right: 0.75rem;
}

.usecase-tile .text {
  font-size: clamp(0.9rem, 2.5vw, 1rem);
}

.tile-group {
  margin-top: 1.5rem;
}

.tile-label {
  font-weight: bold;
  margin-bottom: 0.5rem;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
}

.tile-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.tile-button {
  background-color: #003366;
  color: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  text-align: center;
  transition: background-color 0.2s;
  font-size: clamp(0.85rem, 2.5vw, 0.95rem);
  min-height: 44px;
}

.tile-button:hover {
  background-color: #0055aa;
}

.tile-button.active {
  background-color: #003366;
  font-weight: bold;
  box-shadow: inset 0 0 0 2px white;
}

.tile-scroll-list {
  max-height: 180px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-right: 4px;
  margin-top: 0.5rem;
}

.tile-scroll-list::-webkit-scrollbar {
  width: 6px;
}

.tile-scroll-list::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.4);
  border-radius: 3px;
}

.central-usecases {
  padding: 2rem;
  padding-top: 6rem;
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  margin-top: 6rem;
  height: calc(100vh - 6rem);
  background-color: #f0f4fa;
}

.central-usecase-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, auto);
  gap: 1rem;
  max-width: 700px;
  width: 100%;
  margin: 1rem auto 0;
  justify-content: center;
}

.central-usecase-tile {
  background-color: #004080;
  color: white;
  padding: 1.5rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.central-usecase-tile:hover {
  background-color: #0055aa;
  transform: translateY(-2px);
}

.central-usecase-tile .icon {
  font-size: clamp(1.5rem, 5vw, 2rem);
  margin-bottom: 0.5rem;
}

.central-usecase-tile .name {
  font-size: clamp(1rem, 3.5vw, 1.25rem);
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.central-usecase-tile .description {
  font-size: clamp(0.85rem, 2.5vw, 0.95rem);
  line-height: 1.3;
}

.quiz-warning-banner {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: #6fc198;
  color: #000;
  padding: 1rem 2rem;
  border-radius: 10px;
  font-weight: bold;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  text-align: center;
  animation: fadeInOut 2.5s ease-in-out;
  font-size: clamp(0.9rem, 3vw, 1rem);
}

@keyframes fadeInOut {
  0% {
    opacity: 0;
    transform: translate(-50%, -60%);
  }
  10%,
  90% {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -40%);
  }
}

.quiz-result-popup {
  position: fixed;
  top: 50%;
  left: 61%;
  transform: translate(-50%, -50%) scale(1);
  background-color: #004080;
  color: white;
  padding: 2rem;
  border-radius: 12px;
  z-index: 9999;
  text-align: center;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
  max-width: 90%;
}

.quiz-result-popup button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: white;
  color: #004080;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  min-height: 44px;
  transition: transform 0.2s;
}

.quiz-result-popup button:hover {
  transform: scale(1.05);
}

.popup-enter-active,
.popup-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.popup-enter-from,
.popup-leave-to {
  opacity: 0;
  transform: translate(-50%, -60%) scale(0.8);
}

.usecase-info-modal {
  position: fixed;
  top: 50%;
  left: 61%;
  transform: translate(-50%, -50%);
  background: #004080;
  color: white;
  padding: 2rem;
  border-radius: 12px;
  z-index: 9999;
  text-align: center;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
}

.usecase-info-modal h3 {
  font-size: clamp(1.2rem, 3.5vw, 1.5rem);
  margin: 0 0 1rem;
}

.usecase-info-modal p {
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  margin: 0 0 1rem;
}

.usecase-info-modal button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: white;
  color: #004080;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  min-height: 44px;
}

.quiz-enter-active,
.quiz-leave-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.quiz-enter-from,
.quiz-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.option-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
  transition-delay: calc(0.1s * var(--i));
}
.option-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}
.option-leave-active {
  transition: opacity 0.2s ease;
}
.option-leave-to {
  opacity: 0;
}

.feedback-enter-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.feedback-enter-from {
  opacity: 0;
  transform: scale(0.8);
}
.feedback-leave-active {
  transition: opacity 0.2s ease;
}
.feedback-leave-to {
  opacity: 0;
}

@keyframes bounce {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25%, 75% {
    transform: translateX(-5px);
  }
  50% {
    transform: translateX(5px);
  }
}

.chat-input-wrapper {
  display: flex;
  align-items: center;
  border: 2px solid #c9ddf5;
  border-radius: 12px;
  padding: 0.25rem 0.5rem;
  background-color: #f8fbff;
  box-shadow: 0 0 4px rgba(0, 44, 95, 0.1);
  margin-top: 0.5rem;
}

.chat-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  padding: 0.5rem;
}

.chat-send-button {
  background: none;
  border: none;
  font-size: clamp(1.2rem, 4vw, 1.5rem);
  color: #4a90e2;
  cursor: pointer;
  padding: 0.5rem;
  transition: color 0.2s ease;
  min-height: 44px;
}

.chat-send-button:hover {
  color: #357ab8;
}

.quiz-controls,
.menu-controls {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.cancel-button,
.menu-button {
  background-color: #cc4b37;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-size: clamp(0.9rem, 2.5vw, 1rem);
  min-height: 44px;
}

.cancel-button:hover,
.menu-button:hover {
  background-color: #b04130;
}

.thumb-icon {
  width: 20px;
  height: 20px;
  transition: stroke 0.2s ease;
}

.thumb-button {
  background: transparent;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 0.25rem 0.5rem;
  cursor: pointer;
  transition:
    background-color 0.2s,
    transform 0.1s,
    border-color 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
}

.thumb-button:hover {
  background-color: #e6eef8;
  transform: translateY(-1px);
}

.thumb-button.selected {
  background-color: #d1e7ff;
  border-color: #4a90e2;
}

.thumb-button.selected .thumb-icon {
  stroke: #0053ba;
}

.thumb-button:disabled {
  background-color: #e0e0e0;
  cursor: not-allowed;
  opacity: 0.6;
}

.rating-below {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.3rem;
}

@media (max-width: 828px) {
  #app {
    flex-direction: row;
  }

  .sidebar {
    width: 20vw;
    min-width: 80px;
    padding: 0.5rem;
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    transform: translateX(0);
  }

  .sidebar-hidden {
    transform: translateX(-100%);
  }

  .sidebar-toggle {
    display: block;
  }

  .sidebar-header h2 {
    font-size: 1rem;
  }

  .usecase-grid {
    gap: 0.3rem;
  }

  .usecase-tile {
    flex-direction: column;
    padding: 0.5rem;
    font-size: 0.75rem;
    text-align: center;
  }

  .usecase-tile .emoji {
    font-size: 1.2rem;
    margin-right: 0;
    margin-bottom: 0.3rem;
  }

  .usecase-tile .text {
    font-size: 0.75rem;
  }

  .tile-group {
    margin-top: 1rem;
  }

  .tile-label {
    font-size: 0.8rem;
  }

  .tile-grid {
    grid-template-columns: 1fr;
    gap: 0.3rem;
  }

  .tile-button {
    padding: 0.3rem;
    font-size: 0.7rem;
  }

  .tile-scroll-list {
    max-height: 120px;
    gap: 0.3rem;
  }

  .main {
    margin-left: 20vw;
    height: 100vh;
  }

  .header {
    padding: 0.75rem;
    left: 20vw;
    width: calc(100% - 20vw);
  }

  .header h3 {
    font-size: 1.2rem;
  }

  .header p {
    font-size: 0.85rem;
  }

  .chat {
    padding: 1rem;
  }

  .chat-entry {
    gap: 0.3rem;
  }

  .avatar {
    width: 36px;
    height: 36px;
  }

  .message-content {
    max-width: 85%;
  }

  .bubble {
    padding: 0.75rem;
    font-size: 0.95rem;
  }

  .chat-entry-bot .bubble {
    margin-left: 0.5rem;
  }

  .chat-entry-user .bubble {
    margin-right: 0.5rem;
  }

  .source {
    font-size: 0.8rem;
  }

  .timestamp {
    font-size: 0.7rem;
  }

  .controls {
    padding: 1rem;
  }

  .controls input,
  .controls select,
  .controls button {
    font-size: 0.95rem;
    padding: 0.5rem;
  }

  .chat-input-wrapper {
    padding: 0.2rem 0.4rem;
  }

  .chat-input {
    font-size: 0.95rem;
  }

  .chat-send-button {
    font-size: 1.2rem;
  }

  .quiz-box {
    padding: 1rem;
    max-width: 90%;
  }

  .quiz-progress {
    font-size: 0.85rem;
  }

  .quiz-box h3 {
    font-size: 1.1rem;
  }

  .quiz-box button {
    padding: 0.5rem 1rem;
    font-size: 0.95rem;
  }

  .feedback {
    font-size: 0.95rem;
  }

  .explanation {
    font-size: 0.85rem;
  }

  .central-usecases {
    padding: 1.5rem;
    padding-top: 4rem;
    margin-top: 6rem;
    height: calc(100vh - 6rem);
  }

  .central-usecase-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    max-width: 100%;
    padding: 0 0.5rem;
    margin: 0.75rem auto 0;
  }

  .central-usecase-tile {
    padding: 1rem;
  }

  .central-usecase-tile .icon {
    font-size: 1.5rem;
  }

  .central-usecase-tile .name {
    font-size: 1rem;
  }

  .central-usecase-tile .description {
    font-size: 0.85rem;
  }

  .quiz-warning-banner {
    padding: 0.75rem 1.5rem;
    font-size: 0.95rem;
  }

  .quiz-result-popup {
    padding: 1.5rem;
    max-width: 90%;
  }

  .quiz-result-popup p {
    font-size: 0.95rem;
  }

  .quiz-result-popup button {
    padding: 0.4rem 0.8rem;
    font-size: 0.9rem;
  }

  .usecase-info-modal {
    padding: 1.5rem;
    max-width: 90%;
  }

  .usecase-info-modal h3 {
    font-size: 1.1rem;
  }

  .usecase-info-modal p {
    font-size: 0.9rem;
  }

  .usecase-info-modal button {
    padding: 0.4rem 0.8rem;
    font-size: 0.9rem;
  }

  .thumb-icon {
    width: 18px;
    height: 18px;
  }

  .thumb-button {
    padding: 0.2rem 0.4rem;
  }

  .quiz-controls,
  .menu-controls {
    flex-direction: column;
    gap: 0.3rem;
  }

  .cancel-button,
  .menu-button {
    font-size: 0.9rem;
    padding: 0.4rem 0.8rem;
  }
}

@supports (padding: env(safe-area-inset-bottom)) {
  #app {
    padding-top: env(safe-area-inset-top);
    padding-bottom: env(safe-area-inset-bottom);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
  }

  .controls {
    padding-bottom: calc(1rem + env(safe-area-inset-bottom));
  }

  .sidebar {
    padding-top: calc(1rem + env(safe-area-inset-top));
    padding-bottom: calc(1rem + env(safe-area-inset-bottom));
  }
}

@media (prefers-color-scheme: dark) {
  body {
    background-color: #1e1e1e;
    color: #eee;
  }

  #app {
    background-color: #2c2c2c;
  }

  .sidebar {
    background-color: #121a28;
    color: #fff;
  }

  .main {
    background-color: #1e1e1e;
  }

  .header {
    background-color: #121a28;
    color: #eee;
  }

  .chatbox {
    background-color: #2c2c2c;
  }

  .chat-entry-bot .bubble {
    background-color: #3b3f4c;
    color: #eee;
  }

  .chat-entry-user .bubble {
    background-color: #4a4a4a;
    color: #eee;
  }

  .source {
    color: #aaa;
  }

  .source a {
    color: #5db4ff;
  }

  .timestamp {
    color: #aaa;
  }

  .quiz-box {
    background-color: #3d3d3d;
    border-color: #555;
    color: #eee;
  }

  .quiz-progress {
    color: #ccc;
  }

  .controls {
    background-color: #1b3a57;
  }

  .controls input,
  .controls select {
    background-color: #444;
    color: #fff;
    border: none;
  }

  .controls button {
    background-color: #1b3a57;
    color: #fff;
  }

  .controls button:hover {
    background-color: #224765;
  }

  .quiz-box button {
    background-color: #1b3a57;
  }

  .quiz-box button:hover:not(:disabled) {
    background-color: #224765;
  }

  .quiz-box button.correct {
    background-color: #28a745;
  }

  .quiz-box button.incorrect {
    background-color: #dc3545;
  }

  .feedback {
    color: #5db4ff;
  }

  .explanation {
    color: #aaa;
  }

  .quiz-result-popup {
    background-color: #1f1f1f;
    color: #fff;
  }

  .quiz-result-popup button {
    background-color: #fff;
    color: #1b3a57;
  }

  .usecase-info-modal {
    background-color: #1f1f1f;
    color: #fff;
  }

  .usecase-info-modal button {
    background-color: #fff;
    color: #1b3a57;
  }

  .quiz-warning-banner {
    background-color: #4caf50;
    color: #fff;
  }

  .thumb-button {
    border-color: #555;
  }

  .thumb-button:hover {
    background-color: #3a3f4a;
  }

  .thumb-button.selected {
    background-color: #264b72;
    border-color: #3d84c9;
  }

  .thumb-button.selected .thumb-icon {
    stroke: #cce1ff;
  }

  .thumb-button:disabled {
    background-color: #444;
    cursor: not-allowed;
    opacity: 0.6;
  }

  .tile-button,
  .usecase-tile,
  .central-usecase-tile {
    background-color: #1b3a57;
    color: #fff;
  }

  .tile-button:hover,
  .usecase-tile:hover,
  .central-usecase-tile:hover {
    background-color: #224765;
  }

  .tile-button.active,
  .usecase-tile.active {
    background-color: #16314a;
    font-weight: bold;
    box-shadow: inset 0 0 0 2px #fff;
  }

  .tile-label {
    color: #ccc;
  }

  .tile-scroll-list {
    background-color: #1e1e1e;
  }

  .tile-scroll-list::-webkit-scrollbar-thumb {
    background-color: rgba(255, 255, 255, 0.25);
  }

  .central-usecases {
    background-color: #1e1e1e;
  }

  .central-usecase-tile {
    border: 1px solid #224765;
  }

  .cancel-button,
  .menu-button {
    background-color: #b04130;
  }

  .cancel-button:hover,
  .menu-button:hover {
    background-color: #9c3728;
  }
}
</style>
