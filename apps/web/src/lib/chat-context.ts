export interface ChatContext {
  label: string;
  detail: string;
}

type Listener = (context: ChatContext | null) => void;

let current: ChatContext | null = null;
const listeners = new Set<Listener>();

/**
 * What the chat is currently scoped to.
 *
 * A module-level store rather than React context because the chat is mounted in the root
 * layout and the corpus page is a sibling; threading a provider between them would mean
 * rebuilding the layout for one string.
 *
 * `detail` is the text handed to the model. It must contain only values the page already
 * shows, so scoping the chat can never widen what it knows.
 */
export function setChatContext(context: ChatContext | null): void {
  current = context;
  listeners.forEach((listener) => listener(current));
}

export function getChatContext(): ChatContext | null {
  return current;
}

export function subscribeChatContext(listener: Listener): () => void {
  listeners.add(listener);
  listener(current);
  return () => {
    listeners.delete(listener);
  };
}
