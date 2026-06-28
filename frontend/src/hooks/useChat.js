import { useState, useCallback } from 'react';
import { askQuestion, askQuestionStream } from '../api/client';

export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const getContext = useCallback(() => {
    const pairs = [];
    for (let i = 0; i < messages.length; i += 2) {
      if (messages[i] && messages[i + 1]) {
        pairs.push({
          question: messages[i].content,
          answer: messages[i + 1].content,
        });
      }
    }
    return pairs.slice(-5);
  }, [messages]);

  // Update the most recent assistant message in place (used while streaming).
  const patchLastMessage = useCallback((patch) => {
    setMessages(prev => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last && last.role === 'assistant') {
        next[next.length - 1] = typeof patch === 'function' ? patch(last) : { ...last, ...patch };
      }
      return next;
    });
  }, []);

  const sendMessage = useCallback(async (question) => {
    const context = getContext();
    setMessages(prev => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', isStreaming: true },
    ]);
    setIsLoading(true);

    await askQuestionStream(question, context, {
      onToken: (text) => patchLastMessage(m => ({ ...m, content: m.content + text })),
      onDone: (meta) => patchLastMessage({
        isStreaming: false,
        sources: meta.sources,
        confidence: meta.confidence,
        processingTime: meta.processing_time_ms,
        chunksSearched: meta.chunks_searched,
      }),
      onError: (err) => patchLastMessage({
        isStreaming: false,
        content: `Error: ${err.message}`,
        isError: true,
      }),
    });

    setIsLoading(false);
  }, [getContext, patchLastMessage]);

  // Non-streaming fallback, kept for callers that want a single resolved answer.
  const sendMessageSync = useCallback(async (question) => {
    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const context = getContext();
      const response = await askQuestion(question, context);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        processingTime: response.processing_time_ms,
        chunksSearched: response.chunks_searched,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [getContext]);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, sendMessageSync, clearChat };
}
