import { Fragment, type ReactNode } from 'react';

/** Renders **bold** segments; all other text is shown as-is (React escapes it, so no HTML injection). */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
      <strong key={index} className="font-semibold">
        {part.slice(2, -2)}
      </strong>
    ) : (
      <Fragment key={index}>{part.replace(/\*/g, '')}</Fragment>
    ),
  );
}

const BULLET = /^\s*(?:[-*•]|\d+[.)])\s+/;

/**
 * Light formatting for assistant answers: paragraphs, "- " / "1." lists and **bold**.
 * Stray markdown (headings, lone asterisks) is dropped instead of being shown literally.
 */
export function FormattedText({ text }: { text: string }) {
  const blocks: ReactNode[] = [];
  let items: string[] = [];

  const flushList = () => {
    if (items.length === 0) return;
    blocks.push(
      <ul key={`list-${blocks.length}`} className="list-disc space-y-1 pl-5">
        {items.map((item, index) => (
          <li key={index}>{inline(item)}</li>
        ))}
      </ul>,
    );
    items = [];
  };

  for (const rawLine of text.split('\n')) {
    const line = rawLine.replace(/^\s*#{1,6}\s+/, '').trimEnd();
    if (BULLET.test(line)) {
      items.push(line.replace(BULLET, ''));
      continue;
    }
    flushList();
    if (line.trim()) blocks.push(<p key={`p-${blocks.length}`}>{inline(line.trim())}</p>);
  }
  flushList();

  return <div className="space-y-2">{blocks}</div>;
}
