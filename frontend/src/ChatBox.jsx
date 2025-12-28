import { useState , useRef, useEffect} from "react";
import Message from "./Message";
import ToggleSwitch from "./ToggleSwitch";
import "./chat.css";
import Sidebar from "./Sidebar";
import LoadingDots from "./LoadingDots";


function ChatBox() {
  const [isImageMode, setIsImageMode] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const bottomRef = useRef(null);
  const [generating, setGenerating] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [chatId, setChatId] = useState(null);

  const startNewChat = () => {
    setMessages([]);
    setChatId(null);
    setShowHistory(false);
  };


  useEffect(() => {
    if (generating) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, generating]);

  const openChat = async (chat) => {
    const res = await fetch(`https://smart-ai-c5nt.onrender.com/get-chat/${chat.id}`);
    const data = await res.json();

    // convert backend messages → frontend format
    const formattedMessages = data.map((m) => {
      if (m.role === "user") {
        return { type: "user", text: m.content };
      }

      if (m.type === "image") {
        return { type: "image", url: m.content };
      }

      return { type: "bot", text: m.content ,animate:false};
    });

    // ✅ SET ONCE (loads instantly)
    setMessages(formattedMessages);
    
    setShowHistory(false);
  };
  const handleDelete = (deletedId) => {
    if (chatId === deletedId) {
      setMessages([]);
      setChatId(null);
    }
  };





  const send = async () => {
    if (!input.trim() || generating) return;
    setGenerating(true);

    setMessages((prev) => [...prev, { type: "user", text: input }]);

    const endpoint = isImageMode
      ? "https://smart-ai-c5nt.onrender.com/text-to-image"
      : "https://smart-ai-c5nt.onrender.com/text-to-text";

    let savedResponse = ""; // ✅ store response safely

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: input }),
      });

      if (isImageMode) {
        const data = await res.json();
        savedResponse = data.image_url;

        setMessages((prev) => [
          ...prev,
          { type: "image", url: data.image_url,animate:true },
        ]);
      } else {
        const data = await res.json();
        savedResponse = data.answer;

        setMessages((prev) => [...prev, { type: "bot", text: data.answer,animate:true }]);
      }

      // ✅ SAVE CHAT (NOW WORKS)
      const resSave = await fetch("https://smart-ai-c5nt.onrender.com/save-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          prompt: input,
          response: savedResponse,
          mode: isImageMode ? "image" : "text",
        }),
      });

      const saved = await resSave.json();
      setChatId(saved.chat_id);

    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { type: "bot", text: "❌ Server error",animate:true },
      ]);
    }

    setGenerating(false);
    setInput("");
  };


  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2 className="head">SMART AI</h2>
        <ToggleSwitch isOn={isImageMode} setIsOn={setIsImageMode} />
        <button
          className="history-toggle"
          onClick={() => setShowHistory((v) => !v)}
        >
          {showHistory ? "✖" : "🕘"}
        </button>
      </div>
      {showHistory && (
        <div className="history-panel">
          <Sidebar
            onSelect={(chat) => {
              openChat(chat);
              setShowHistory(false);
            }}
            onNewChat={startNewChat}
            onDelete={handleDelete}
          />
        </div>
      )}

      <div className="chat-body">
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}

        {generating && <LoadingDots />}

        <div ref={bottomRef} />
      </div>

      <div className="input-row">
        <input
          placeholder={isImageMode ? "Describe image..." : "Ask something..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />

        <button className="send-btn" onClick={send} disabled={generating}>
          {generating ? (
            <span className="btn-dots">
              <i></i>
              <i></i>
              <i></i>
            </span>
          ) : (
            "⬆"
          )}
        </button>
      </div>
    </div>
  );
}

export default ChatBox;
