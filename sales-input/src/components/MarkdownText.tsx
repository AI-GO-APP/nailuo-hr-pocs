import React from "react";
export default function MarkdownText({ text }: { text: string }) {
  if (!text) return null;
  const html = text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}
