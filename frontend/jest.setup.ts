import "@testing-library/jest-dom";

// jsdom does not implement scrollTo -- components that auto-scroll a
// message list (ChatPanel) need a no-op so effects don't throw in tests.
if (typeof Element !== "undefined" && !Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {};
}
