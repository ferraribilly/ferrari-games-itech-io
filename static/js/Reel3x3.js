import Symbol from "./Symbol3x3.js";

export default class Reel {
  constructor(reelContainer, idx, initialSymbols) {
    this.reelContainer = reelContainer;
    this.idx = idx;

    this.symbolContainer = document.createElement("div");
    this.symbolContainer.classList.add("icons");
    this.reelContainer.appendChild(this.symbolContainer);

    initialSymbols.forEach(name => {
      this.symbolContainer.appendChild(new Symbol(name).el);
    });
  }

  get factor() {
    return 1 + Math.pow(this.idx / 2, 2);
  }

  renderSymbols(nextSymbols) {
    const fragment = document.createDocumentFragment();
    const total = Math.floor(this.factor) * 3;

    for (let i = 0; i < total; i++) {
      const sym = new Symbol(
        i >= total - 3 ? nextSymbols[i - (total - 3)] : Symbol.random()
      );
      fragment.appendChild(sym.el);
    }

    this.symbolContainer.appendChild(fragment);
  }

  spin() {
    this.symbolContainer.style.transition = "transform 0.6s cubic-bezier(.2,.7,.3,1)";
    this.symbolContainer.style.transform = "translateY(-300%)";

    return new Promise(resolve => {
      setTimeout(() => {
        this.symbolContainer.style.transition = "none";
        this.symbolContainer.style.transform = "translateY(0)";
        const max = this.symbolContainer.children.length - 3;
        for (let i = 0; i < max; i++) {
          this.symbolContainer.firstChild.remove();
        }
        resolve();
      }, 600);
    });
  }

  highlightRow(row) {
    const items = this.symbolContainer.children;
    if (items[row]) items[row].classList.add("win");
  }
}
