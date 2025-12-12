const cache = {};

const urls = {
  "1": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239832/pngwing.com_p82ete.png",
  "2": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239833/pngwing.com_4_tmg4yk.png",
  "3": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239833/pngwing.com_1_juxkdx.png",
  "4": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239833/pngwing.com_5_wdtgo5.png",
  "5": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239832/pngwing.com_2_gs3hah.png",
  "6": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765239832/pngwing.com_3_kgtmml.png",
  "7": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765202647/duende_pqddrf.png",
  "8": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765202646/cofre_u8pj8q.png",
  "9": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765463864/dre_xcgzon.png"
  
};

export default class Symbol {
  constructor(name = Symbol.random()) {
    this.name = name;

    if (cache[name]) {
      this.img = cache[name].cloneNode();
    } else {
      this.img = new Image();
      this.img.src = urls[name];
      cache[name] = this.img;
    }

    // tamanho ideal para 3x3
    this.img.classList.add("symbol");
  }

  static preload() {
    Symbol.symbols.forEach(s => new Symbol(s));
  }

  static get symbols() {
    return [
     "1",
     "2",
     "3",
     "4",
     "5",
     "6", 
     "7",
     "8",
     "9"
    ];
  }

  static random() {
    return this.symbols[Math.floor(Math.random() * this.symbols.length)];
  }
}
