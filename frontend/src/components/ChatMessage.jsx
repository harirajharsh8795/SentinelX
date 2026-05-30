import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ChatMessage({ content }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ node, ...props }) => <h1 className="text-teal-400 text-xl font-bold mt-4 mb-2 border-b border-teal-800" {...props} />,
        h2: ({ node, ...props }) => <h2 className="text-teal-300 text-lg font-semibold mt-4 mb-2" {...props} />,
        h3: ({ node, ...props }) => <h3 className="text-white text-base font-semibold mt-3 mb-1" {...props} />,
        p: ({ node, ...props }) => <p className="text-gray-300 mb-3 leading-relaxed" {...props} />,
        ul: ({ node, ...props }) => <ul className="list-disc ml-4 mb-3 space-y-1" {...props} />,
        ol: ({ node, ...props }) => <ol className="list-decimal ml-4 mb-3 space-y-1" {...props} />,
        li: ({ node, ...props }) => <li className="text-gray-300" {...props} />,
        strong: ({ node, ...props }) => <strong className="text-white font-semibold" {...props} />,
        table: ({ node, ...props }) => <table className="w-full border-collapse mb-4" {...props} />,
        th: ({ node, ...props }) => <th className="text-teal-400 border border-gray-700 px-3 py-2 text-left text-sm" {...props} />,
        td: ({ node, ...props }) => <td className="text-gray-300 border border-gray-700 px-3 py-2 text-sm" {...props} />,
        code: ({ node, ...props }) => <code className="bg-gray-800 text-teal-300 px-1 rounded text-sm" {...props} />,
        blockquote: ({ node, ...props }) => <blockquote className="border-l-2 border-teal-500 pl-3 italic text-gray-400" {...props} />,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}
