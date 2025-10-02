import MessageBubble from "./MessageBubble";

function MessageList({ messages }) {
  return (
    <div style={{ flex: 1, overflowY: "auto", padding: "1rem" }}>
      {messages.map((msg, i) => (
        <MessageBubble key={i} sender={msg.sender} text={msg.text} />
      ))}
    </div>
  );
}

export default MessageList;
