const cache = {};

const urls = {
   "1": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765202646/farao_prc8ws.png",
   "2": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221103/ra_mwntdu.png",
   "3": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221103/ra1_vi5gig.png",
   "4": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221103/mascara_dw0qep.png",
   "5": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221102/cubo_j33zb4.png",
   "6": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221102/gata_bwynlj.png",
   "7": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221102/cleopta_oog5fz.png",
   "8": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221102/placa_wrqvbr.png",
   "9": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765221102/piramide_rikoly.png",
   "10": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765203732/symbol1_rnaorb.png",
   "11": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765203729/symbol2_d8sc8h.png",
   "12": 'https://res.cloudinary.com/dptprh0xk/image/upload/v1765203729/munra_a2mkda.png',
   "13": 'https://res.cloudinary.com/dptprh0xk/image/upload/v1765203728/farao2_x5ckd9.png',
   "14": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765203728/farao3_yuc1tz.png",
   "15": "https://res.cloudinary.com/dptprh0xk/image/upload/v1765203728/farao1_yvcqob.png"

  
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
     "9",
     "10",
     "11",
     "12",
     "13",
     "14",
     "15"
    ];
  }

  static random() {
    return this.symbols[Math.floor(Math.random() * this.symbols.length)];
  }
}
