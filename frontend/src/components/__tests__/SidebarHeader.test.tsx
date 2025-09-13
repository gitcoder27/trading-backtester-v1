import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from '../layout/Sidebar';
import Header from '../layout/Header';
import { useUIStore } from '../../stores/uiStore';

describe('Sidebar', () => {
  beforeEach(() => {
    useUIStore.setState({ sidebarOpen: true, theme: 'dark', notifications: [] });
  });

  it('shows overlay when open and closes on click', () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>
    );
    const overlay = document.querySelector('.fixed.inset-0') as HTMLElement;
    expect(overlay).toBeTruthy();
    fireEvent.click(overlay);
    expect(useUIStore.getState().sidebarOpen).toBe(false);
  });
});

describe('Header', () => {
  it('renders and toggles sidebar via button', () => {
    useUIStore.setState({ sidebarOpen: false, theme: 'dark', notifications: [] });
    render(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );
    const btn = screen.getByRole('button', { name: /toggle sidebar/i });
    fireEvent.click(btn);
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });
});

