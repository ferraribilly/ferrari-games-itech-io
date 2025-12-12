const cache = {};

const urls = {
   "1": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765202646/cofre_u8pj8q.png",
   "2": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765202646/porquinho_fpuuds.png",
   "3": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765238904/tigrao_rveqok.png",
   "4": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765411421/pngwing.com_4_wdf0ax.png",
   "5": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765238904/tourinho_f7nszf.png",
   "6": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765238903/sete_rvmd4y.png",
   "7": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765238903/sacodinheiro_e5pkyi.png",
   "8": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765216932/pngwing.com_x7b7mf.png",
   "9": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765486793/pngwing.com_9_dp7otf.png"
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
