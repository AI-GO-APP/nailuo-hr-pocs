import React from "react";

/**
 * 輕量 Markdown 渲染元件
 * 支援：**粗體**、*斜體*、- 無序列表、1. 有序列表、換行
 */
export default function MarkdownText({ text }: { text: string }) {
  if (!text) return null;

  // 按段落分割（雙換行 or 單換行）
  const blocks = text.split(/\n/).map(l => l.trimEnd());

  const rendered: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let idx = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const Tag = listType === "ol" ? "ol" : "ul";
    rendered.push(
      <Tag key={`list-${idx++}`} className="md-list">
        {listItems.map((item, i) => <li key={i}>{inlineParse(item)}</li>)}
      </Tag>
    );
    listItems = [];
    listType = null;
  };

  for (const line of blocks) {
    // 空行 → flush
    if (!line.trim()) {
      flushList();
      continue;
    }

    // 無序列表：- 或 * 開頭
    const ulMatch = line.match(/^[\-\*]\s+(.+)/);
    if (ulMatch) {
      if (listType === "ol") flushList();
      listType = "ul";
      listItems.push(ulMatch[1]);
      continue;
    }

    // 有序列表：1. 2. 等
    const olMatch = line.match(/^\d+[\.\)]\s*(.+)/);
    if (olMatch) {
      if (listType === "ul") flushList();
      listType = "ol";
      listItems.push(olMatch[1]);
      continue;
    }

    // 非列表 → flush 之前的列表
    flushList();

    // 普通段落
    rendered.push(<p key={`p-${idx++}`} className="md-p">{inlineParse(line)}</p>);
  }

  flushList();

  return <div className="md-content">{rendered}</div>;
}

/** inline 解析：**粗體**、*斜體* */
function inlineParse(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  // 用 regex 匹配 **bold** 和 *italic*
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    // 前面的純文字
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[2]) {
      // **bold**
      parts.push(<strong key={key++}>{match[2]}</strong>);
    } else if (match[3]) {
      // *italic*
      parts.push(<em key={key++}>{match[3]}</em>);
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length ? parts : [text];
}
