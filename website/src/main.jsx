import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';
import { Toaster } from 'react-hot-toast';
import App from './App';
import { SiteProvider } from './context/SiteContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <SiteProvider>
          <App />
          <Toaster
              position="top-right"
              toastOptions={{
                style: { borderRadius: '14px', background: '#25104A', color: '#fff', fontSize: '14px' },
                success: { iconTheme: { primary: '#E9BE3B', secondary: '#25104A' } },
              }}
            />
        </SiteProvider>
      </BrowserRouter>
    </HelmetProvider>
  </React.StrictMode>,
);
