import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Message({ msg }) {
  const [displayText, setDisplayText] = useState("");
  

  useEffect(() => {
    if (msg.type !== "bot") return;

    // ✅ NO animation → show instantly
    if (msg.animate === false) {
      setDisplayText(msg.text);
      return;
    }

    // ✅ Animate only for new messages
    let i = 0;
    setDisplayText("");

    const interval = setInterval(() => {
      setDisplayText(msg.text.slice(0, i + 1));
      i++;
      if (i >= msg.text.length) clearInterval(interval);
    }, 12);

    return () => clearInterval(interval);
  }, [msg.text, msg.type, msg.animate]);

  if (msg.type === "user") {
    return <div className="msg user">{msg.text}</div>;
  }

  if (msg.type === "bot") {
    return (
      <div className="msg bot fade-in">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayText}</ReactMarkdown>
      </div>
    );
  }

  if (msg.type === "image") {
    return (
      <div className="msg bot fade-in">
        <img src={msg.url} alt="AI" />
      </div>
    );
  }
  
  return null;
}

export default Message;
