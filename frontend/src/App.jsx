import Header from "./components/Header";
import MessageList from "./components/MessageList";
import InputBar from "./components/InputBar";
import { useChat } from "./hooks/useChat";

function App() {
  const { messages, sendMessage } = useChat();

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        background: "#eceff1",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          maxWidth: "600px",
          height: "90vh",
          borderRadius: "12px",
          overflow: "hidden",
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          background: "#fff",
        }}
      >
        <Header />
        <MessageList messages={messages} />
        <InputBar onSend={sendMessage} />
      </div>
    </div>
  );
}

export default App;
