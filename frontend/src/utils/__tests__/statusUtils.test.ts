import { describe, it, expect } from 'vitest';
import { getStatusIcon, getStatusVariant, getStatusColor } from '../status';
import { CheckCircle, Play, XCircle, Square, Clock } from 'lucide-react';

describe('status helpers', () => {
  it('returns expected icon for each status', () => {
    expect(getStatusIcon('completed')).toBe(CheckCircle);
    expect(getStatusIcon('running')).toBe(Play);
    expect(getStatusIcon('failed')).toBe(XCircle);
    expect(getStatusIcon('cancelled')).toBe(Square);
    expect(getStatusIcon('pending')).toBe(Clock);
  });

  it('maps status to variants', () => {
    expect(getStatusVariant('completed')).toBe('success');
    expect(getStatusVariant('running')).toBe('primary');
    expect(getStatusVariant('failed')).toBe('danger');
    expect(getStatusVariant('cancelled')).toBe('secondary');
    expect(getStatusVariant('pending')).toBe('warning');
  });

  it('returns correct color class', () => {
    expect(getStatusColor('completed')).toBe('text-green-500');
    expect(getStatusColor('running')).toBe('text-blue-500');
    expect(getStatusColor('failed')).toBe('text-red-500');
    expect(getStatusColor('cancelled')).toBe('text-gray-500');
    expect(getStatusColor('pending')).toBe('text-yellow-500');
    expect(getStatusColor('unknown')).toBe('text-yellow-500');
  });
});
