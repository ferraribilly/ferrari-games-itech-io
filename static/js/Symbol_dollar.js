const cache = {};

const urls = {
  // DOLLAR 3x3=9
   "1": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407069/pngwing.com_7_zxx6cn.png",
   "2": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407068/pngwing.com_9_pjxpa3.png",
   "3": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407068/pngwing.com_8_m8ndaw.png",
   "4": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407067/pngwing.com_10_kng23m.png",
   "5": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407067/pngwing.com_14_orcqyk.png",
   "6": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407066/pngwing.com_12_tkkukk.png",
   "7": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407066/pngwing.com_13_x5ureq.png",
   "8": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407065/pngwing.com_11_bjnjjj.png",
   "9": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765407065/bitcoin_pjo40b.png"
   
  
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
     "1",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "2",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "3",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "4",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "5",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "6",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "7",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "8",  //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
     "9"   //value 0.25 3x  //value 0.50 6x  //value 0.75 9x
    ];
  }

  static random() {
    return this.symbols[Math.floor(Math.random() * this.symbols.length)];
  }
}
