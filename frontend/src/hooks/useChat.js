import { useState, useCallback } from 'react';
import { askQuestion } from '../api/client';

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

  const sendMessage = useCallback(async (question) => {
    const userMsg = { role: 'user', content: question };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const context = getContext();
      const response = await askQuestion(question, context);
      const aiMsg = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidence: response.confidence,
        processingTime: response.processing_time_ms,
        chunksSearched: response.chunks_searched,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: `Error: ${err.message}`,
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [getContext]);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  return { messages, isLoading, sendMessage, clearChat };
}
