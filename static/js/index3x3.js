import Slot from "./Slot3x3.js";

const config = {
  inverted: false, // true: reels spin from top to bottom; false: reels spin from bottom to top
  onSpinStart: (symbols) => {
    console.log("onSpinStart", symbols);
  },
  onSpinEnd: (symbols) => {
    console.log("onSpinEnd", symbols);
  },
};

const slotCanvas = new Slot(document.getElementById("slotCanvas"), config);
