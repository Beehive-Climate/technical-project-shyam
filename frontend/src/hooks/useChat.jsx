import { useState } from "react";

export function useChat() {
  const [messages, setMessages] = useState([]);

  const sendMessage = async (query) => {
    if (!query.trim()) return;

    setMessages((prev) => [...prev, { sender: "user", text: query }]);
    setMessages((prev) => [...prev, { sender: "bot", text: "" }]);

    try {
      const response = await fetch("http://127.0.0.1:8000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let botMessage = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        botMessage += decoder.decode(value, { stream: true });

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1].text = botMessage;
          return updated;
        });
      }
    } catch {
      setMessages((prev) => [...prev, { sender: "bot", text: "⚠️ Error streaming response" }]);
    }
  };

  return { messages, sendMessage };
}
