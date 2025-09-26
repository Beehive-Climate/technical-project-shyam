import ReactMarkdown from "react-markdown";

function MessageBubble({ sender, text }) {
  const isUser = sender === "user";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "0.75rem",
      }}
    >
      {isUser ? (
        <span
          style={{
            maxWidth: "70%",
            padding: "0.6rem 1rem",
            borderRadius: "18px",
            background: "#4caf50",
            color: "#fff",
            fontSize: "0.95rem",
          }}
        >
          {text}
        </span>
      ) : (
        <div
          style={{
            maxWidth: "70%",
            padding: "0.6rem 1rem",
            borderRadius: "12px",
            background: "#fffbe6",
            border: "1px solid #ffcc33",
            fontSize: "0.95rem",
            color: "#333",
          }}
        >
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default MessageBubble;
