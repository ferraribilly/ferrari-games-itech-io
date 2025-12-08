const cache = {};

const urls = {
  "avestruz": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547489/avestruz_pur9xf.jpg",
  "aguia": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547488/aguia_rqrgow.jpg",
  "burro": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547479/burro_nhqsuo.jpg",
  "borboleta": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547475/borboleta_dvxbt5.jpg",
  "cachorro": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547474/cachorro_sbxa0t.jpg",
  "cabra": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547463/cabra_syobez.jpg",
  "carneiro": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547462/carneiro_el5q8c.jpg",
  "camelo": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547462/camelo_zvqiib.jpg",
  "cobra": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547449/cobra_vsptji.jpg",
  "coelho": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547449/coelho_w3svli.jpg",
  "galo": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547449/galo_xblsct.jpg",
  "cavalo": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547438/cavalo_nfpnhr.jpg",
  "elefante": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547437/elefante_oogtdd.jpg",
  "gato": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547436/gato_zci9oe.jpg",
  "jacare": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547430/jacare_teict1.jpg",
  "leao": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547430/leao_ri1qwk.jpg",
  "macaco": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547430/macaco_bxswmk.jpg",
  "porco": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547425/porco_vidqjm.jpg",
  "pavao": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547425/pavao_ulyvcg.jpg",
  "peru": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547419/peru_jktqmx.jpg",
  "tigre": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547419/tigre_c89mmi.jpg",
  "touro": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547419/touro_ydodxb.jpg",
  "urso": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547419/urso_xgaypz.jpg",
  "veado": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547418/viado_p08gzp.jpg",
  "vaca": "https://res.cloudinary.com/dptprh0xk/image/upload/v1762547418/vaca_x2m2gl.jpg"
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
      "avestruz","aguia","burro","borboleta","cachorro","cabra",
      "carneiro","camelo","cobra","coelho","cavalo","elefante",
      "galo","gato","jacare","leao","macaco","porco","pavao",
      "peru","touro","tigre","urso","veado","vaca"
    ];
  }

  static random() {
    return this.symbols[Math.floor(Math.random() * this.symbols.length)];
  }
}
