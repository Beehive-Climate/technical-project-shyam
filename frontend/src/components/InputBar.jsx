import { useState } from "react";

function InputBar({ onSend }) {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (input.trim()) {
      onSend(input);
      setInput("");
    }
  };

  return (
    <div
      style={{
        display: "flex",
        padding: "0.75rem",
        borderTop: "1px solid #ddd",
        background: "#fafafa",
      }}
    >
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSend()}
        placeholder="Ask about climate risks..."
        style={{
          flex: 1,
          padding: "0.75rem 1rem",
          borderRadius: "20px",
          border: "1px solid #ccc",
          outline: "none",
          fontSize: "1rem",
        }}
      />
      <button
        onClick={handleSend}
        style={{
          marginLeft: "0.5rem",
          padding: "0.6rem 1rem",
          borderRadius: "50%",
          border: "none",
          background: "#4caf50",
          color: "#fff",
          fontSize: "1rem",
          cursor: "pointer",
        }}
      >
        ➤
      </button>
    </div>
  );
}

export default InputBar;
