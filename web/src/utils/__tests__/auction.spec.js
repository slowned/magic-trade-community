import { describe, it, expect } from 'vitest';
import { formatArs, formatCountdown, urgencyClass, toLocalInputValue } from '@/utils/auction';

describe('formatArs', () => {
  it('formats a decimal string as pesos with no cents', () => {
    expect(formatArs('12500.00')).toMatch(/12\.500/);
  });

  it('renders a dash for missing amounts', () => {
    expect(formatArs(null)).toBe('—');
    expect(formatArs('')).toBe('—');
  });
});

describe('formatCountdown', () => {
  it('drops to days and hours when the close is far away', () => {
    expect(formatCountdown(3 * 86400 + 4 * 3600)).toBe('3d 4h');
  });

  it('shows hours and minutes within a day', () => {
    expect(formatCountdown(4 * 3600 + 12 * 60)).toBe('4h 12m');
  });

  it('counts seconds in the last hour', () => {
    expect(formatCountdown(12 * 60 + 5)).toBe('12m 05s');
  });

  it('reports a finished auction as closed', () => {
    expect(formatCountdown(0)).toBe('Cerrada');
  });
});

describe('urgencyClass', () => {
  it('flags the anti-snipe window as critical', () => {
    expect(urgencyClass(120)).toBe('critical');
  });

  it('flags the last hour as urgent', () => {
    expect(urgencyClass(1800)).toBe('urgent');
  });

  it('leaves anything further out alone', () => {
    expect(urgencyClass(86400)).toBe('normal');
    expect(urgencyClass(0)).toBe('ended');
  });
});

describe('toLocalInputValue', () => {
  it('produces a datetime-local value without a timezone suffix', () => {
    expect(toLocalInputValue('2026-08-28T21:00:00Z')).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
  });

  it('is empty for a missing date', () => {
    expect(toLocalInputValue(null)).toBe('');
  });
});
