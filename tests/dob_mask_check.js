const assert = require("node:assert/strict");
const { formatDobValue, caretForDigitCount, nextDobState } = require("../static/js/dob-input.js");

assert.equal(formatDobValue("15082012"), "15/08/2012");
assert.equal(formatDobValue("01012010"), "01/01/2010");
assert.equal(formatDobValue("15/08/2012"), "15/08/2012");
assert.equal(formatDobValue("15a08b2012"), "15/08/2012");
assert.equal(formatDobValue("1508"), "15/08");
assert.equal(formatDobValue("1508201299"), "15/08/2012");

let state = { value: "", caret: 0 };
for (const digit of "15082012") {
  state = nextDobState(state.value, state.caret, state.caret, { type: "insert", text: digit });
}
assert.equal(state.value, "15/08/2012");
assert.equal(state.caret, 10);

state = nextDobState("", 0, 0, { type: "insert", text: "01012010" });
assert.equal(state.value, "01/01/2010");
assert.equal(state.caret, 10);

state = nextDobState("15/08/2012", 10, 10, { type: "backspace" });
assert.equal(state.value, "15/08/201");
assert.equal(state.caret, 9);

state = nextDobState("15/08/2012", 3, 3, { type: "backspace" });
assert.equal(state.value, "10/82/012");
assert.equal(state.caret, 1);

state = nextDobState("15/08/2012", 2, 2, { type: "delete" });
assert.equal(state.value, "15/82/012");
assert.equal(state.caret, 2);

state = nextDobState("15/08/2012", 6, 6, { type: "insert", text: "99" });
assert.equal(state.value, "15/08/9920");
assert.equal(state.caret, 8);

assert.equal(caretForDigitCount("15/08/2012", 4), 5);
assert.equal(caretForDigitCount("15/08/2012", 0), 0);

console.log("dob mask ok");
