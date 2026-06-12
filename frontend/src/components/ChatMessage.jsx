import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatMessage({ content, isNew }) {
  const [displayedText, setDisplayedText] = useState(isNew ? "" : content);
  const indexRef = useRef(0);

  useEffect(() => {
    if (!isNew || !content) {
      setDisplayedText(content);
      return;
    }

    setDisplayedText("");
    indexRef.current = 0;
    
    const words = content.split(" ");
    let currentText = "";
    
    const interval = setInterval(() => {
      if (indexRef.current < words.length) {
        currentText += (indexRef.current === 0 ? "" : " ") + words[indexRef.current];
        setDisplayedText(currentText);
        indexRef.current++;
      } else {
        clearInterval(interval);
      }
    }, 20); // 20ms per word is organic typing speed

    return () => clearInterval(interval);
  }, [content, isNew]);

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h2: ({...props}) => 
          <h2 className="text-teal-400 text-base font-bold mt-4 mb-2 border-b border-teal-900 pb-1" {...props}/>,
        h3: ({...props}) => 
          <h3 className="text-teal-300 text-sm font-semibold mt-3 mb-1" {...props}/>,
        p: ({...props}) => 
          <p className="text-gray-300 mb-2 leading-relaxed text-sm" {...props}/>,
        ul: ({...props}) => 
          <ul className="list-disc ml-4 mb-2 space-y-1 text-gray-300 text-sm" {...props}/>,
        ol: ({...props}) => 
          <ol className="list-decimal ml-4 mb-2 space-y-1 text-gray-300 text-sm" {...props}/>,
        li: ({...props}) => 
          <li className="text-gray-300" {...props}/>,
        strong: ({...props}) => 
          <strong className="text-white font-semibold" {...props}/>,
        table: ({...props}) => 
          <div className="overflow-x-auto mb-3"><table className="w-full border-collapse text-xs" {...props}/></div>,
        th: ({...props}) => 
          <th className="border border-gray-700 px-2 py-1 text-teal-400 text-left bg-gray-900" {...props}/>,
        td: ({...props}) => 
          <td className="border border-gray-700 px-2 py-1 text-gray-300" {...props}/>,
        blockquote: ({...props}) => 
          <blockquote className="border-l-2 border-teal-500 pl-3 italic text-gray-400 my-2" {...props}/>,
        code: ({...props}) => 
          <code className="bg-gray-800 text-teal-300 px-1 rounded text-sm" {...props}/>,
      }}
    >
      {displayedText}
    </ReactMarkdown>
  );
}
