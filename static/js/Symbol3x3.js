const cache = {};

// EMOJIS HTML ENCODED (SEM BICHOS)
const emojis = {
  "diamante": "&#128142;",     // 💎
  "fogo": "&#128293;",         // 🔥
  "raio": "&#9889;",           // ⚡
  "estrela": "&#11088;",        // ⭐
  "coroa": "&#128081;",        // 👑
  "dinheiro": "&#128176;",     // 💰
  "sino": "&#128276;",         // 🔔
  "alvo": "&#127919;",         // 🎯
  "trofeu": "&#127942;",       // 🏆
  "joia": "&#128142;",         // 💎
  "baralho": "&#127183;",      // 🃏
  "dados": "&#127922;",        // 🎲
  "foguete": "&#128640;",      // 🚀
  "chave": "&#128273;",        // 🔑
  "bomba": "&#128163;",        // 💣
  "magia": "&#10024;",         // ✨
  "anel": "&#128141;",         // 💍
  "medalha": "&#127941;",      // 🥇
  "diamante_vermelho": "&#128315;", // 🔻
  "diamante_azul": "&#128312;"    // 🔷
};

export default class Symbol {
  constructor(name = Symbol.random()) {
    this.name = name;

    if (cache[name]) {
      this.el = cache[name].cloneNode(true);
    } else {
      this.el = document.createElement("div");
      this.el.classList.add("emoji-symbol");

      // USANDO HTML ENCODED
      this.el.innerHTML = emojis[name];

      this.el.style.fontSize = "clamp(40px, 8vw, 80px)";
      this.el.style.lineHeight = "1";
      this.el.style.display = "flex";
      this.el.style.alignItems = "center";
      this.el.style.justifyContent = "center";

      cache[name] = this.el;
    }
  }

  static preload() {
    Symbol.symbols.forEach((symbol) => new Symbol(symbol));
  }

  static get symbols() {
    return [
      "diamante",
      "fogo",
      "raio",
      "estrela",
      "coroa",
      "dinheiro",
      "sino",
      "alvo",
      "trofeu",
      "joia",
      "baralho",
      "dados",
      "foguete",
      "chave",
      "bomba",
      "magia",
      "anel",
      "medalha",
      "diamante_vermelho",
      "diamante_azul"
    ];
  }

  static random() {
    return this.symbols[Math.floor(Math.random() * this.symbols.length)];
  }
}
