import { createRoot } from "react-dom/client";

import { App } from "./App";
import "./styles.css";

if (import.meta.env.DEV) {
  void import("react-scan");
  void import("react-grab");
}

const root = document.getElementById("nfi-react-root");

if (root === null) {
  throw new Error("NFI React root was not found.");
}

createRoot(root).render(<App />);
