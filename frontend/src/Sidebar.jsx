import { useEffect, useState } from "react";
import "./SB.css";
function Sidebar({ onSelect, onNewChat, onDelete }) {
  const [history, setHistory] = useState([]);

  const loadHistory = () => {
    fetch("http://localhost:5000/get-chats")
      .then((res) => res.json())
      .then((data) => setHistory(data));
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const deleteChat = async (id) => {
    await fetch(`http://localhost:5000/delete-chat/${id}`, {
      method: "DELETE",
    });
    loadHistory(); // refresh sidebar
    onDelete(id); // notify ChatBox
  };

  return (
    <div className="sidebar">
      <div className="new-chat" onClick={onNewChat}>
        ➕ New Chat
      </div>

      <h4>History</h4>

      {history.map((chat) => (
        <div key={chat.id} className="history-row">
          <span className="history-link" onClick={() => onSelect(chat)}>
            {(chat.title || "New Chat").slice(0, 30)}
          </span>

          <button
            className="delete-btn"
            onClick={(e) => {
              e.stopPropagation(); // ❗ prevent open
              deleteChat(chat.id);
            }}
          >
            🗑️
          </button>
        </div>
      ))}
    </div>
  );
}

export default Sidebar;
