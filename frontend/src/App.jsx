import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';

// Layouts
import { PublicLayout } from './layouts/PublicLayout';
import { AuthLayout } from './layouts/AuthLayout';
import { DashboardLayout } from './layouts/DashboardLayout';

// Auth Pages
import { LoginRootPage } from './pages/auth/LoginRootPage';
import { LoginPage } from './pages/auth/LoginPage';
import { SignupPage } from './pages/auth/SignupPage';
import { VerifyEmailPage } from './pages/auth/VerifyEmailPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { OnboardingPage } from './pages/auth/OnboardingPage';

// Public Marketing Pages
import { HomePage } from './pages/public/HomePage';
import { FeaturesPage } from './pages/public/FeaturesPage';
import { HowItWorksPage } from './pages/public/HowItWorksPage';
import { ModelsPage } from './pages/public/ModelsPage';
import { PricingPage } from './pages/public/PricingPage';
import { AboutPage } from './pages/public/AboutPage';
import { FaqPage } from './pages/public/FaqPage';
import { ContactPage } from './pages/public/ContactPage';
import { PrivacyPage } from './pages/public/PrivacyPage';
import { TermsPage } from './pages/public/TermsPage';
import { RefundPolicyPage } from './pages/public/RefundPolicyPage';
import { CookiePolicyPage } from './pages/public/CookiePolicyPage';

// App / Dashboard Pages
import { DashboardHome } from './pages/app/DashboardHome';
import { WarRoomPage } from './pages/app/WarRoomPage';
import { ArenaNewPage } from './pages/app/ArenaNewPage';
import { ArenaViewPage } from './pages/app/ArenaViewPage';
import { HistoryPage } from './pages/app/HistoryPage';
import { SavedAnswersPage } from './pages/app/SavedAnswersPage';
import { AppModelsPage } from './pages/app/AppModelsPage';
import { UsagePage } from './pages/app/UsagePage';
import { BillingPage } from './pages/app/BillingPage';
import { BillingManagePage } from './pages/app/BillingManagePage';
import { BillingInvoicesPage } from './pages/app/BillingInvoicesPage';
import { BillingUpgradePage } from './pages/app/BillingUpgradePage';
import { ProfileSettings } from './pages/app/ProfileSettings';
import { SecuritySettings } from './pages/app/SecuritySettings';
import { PreferencesSettings } from './pages/app/PreferencesSettings';

// Checkout Pages
import { CheckoutPage } from './pages/checkout/CheckoutPage';
import { CheckoutSuccessPage } from './pages/checkout/CheckoutSuccessPage';
import { CheckoutCancelledPage } from './pages/checkout/CheckoutCancelledPage';
import { CheckoutFailedPage } from './pages/checkout/CheckoutFailedPage';

// Error 404
import { NotFoundPage } from './pages/NotFoundPage';

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Root Route: Branded Sangram AI Login Experience with Animated Arena & Form Reveal */}
            <Route path="/" element={<LoginRootPage />} />

            {/* Standard Auth Routes (Wrapped in AuthLayout) */}
            <Route element={<AuthLayout />}>
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/signup" element={<SignupPage />} />
              <Route path="/auth/verify-email" element={<VerifyEmailPage />} />
              <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
              <Route path="/onboarding" element={<OnboardingPage />} />
            </Route>

            {/* Public Marketing Website (Wrapped in PublicLayout) */}
            <Route element={<PublicLayout />}>
              <Route path="/home" element={<HomePage />} />
              <Route path="/features" element={<FeaturesPage />} />
              <Route path="/how-it-works" element={<HowItWorksPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/pricing" element={<PricingPage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/faq" element={<FaqPage />} />
              <Route path="/contact" element={<ContactPage />} />
              <Route path="/privacy" element={<PrivacyPage />} />
              <Route path="/terms" element={<TermsPage />} />
              <Route path="/refund-policy" element={<RefundPolicyPage />} />
              <Route path="/cookie-policy" element={<CookiePolicyPage />} />
              <Route path="/cookies" element={<CookiePolicyPage />} />
            </Route>

            {/* SaaS Dashboard Shell (Wrapped in DashboardLayout) */}
            <Route path="/app" element={<DashboardLayout />}>
              <Route index element={<DashboardHome />} />
              <Route path="war-room" element={<WarRoomPage />} />
              <Route path="arena" element={<ArenaNewPage />} />
              <Route path="arena/new" element={<ArenaNewPage />} />
              <Route path="arena/:id" element={<ArenaViewPage />} />
              <Route path="history" element={<HistoryPage />} />
              <Route path="saved" element={<SavedAnswersPage />} />
              <Route path="models" element={<AppModelsPage />} />
              <Route path="usage" element={<UsagePage />} />
              <Route path="billing" element={<BillingPage />} />
              <Route path="billing/manage" element={<BillingManagePage />} />
              <Route path="billing/invoices" element={<BillingInvoicesPage />} />
              <Route path="billing/upgrade" element={<BillingUpgradePage />} />
              <Route path="settings" element={<Navigate to="/app/settings/profile" replace />} />
              <Route path="settings/profile" element={<ProfileSettings />} />
              <Route path="settings/security" element={<SecuritySettings />} />
              <Route path="settings/preferences" element={<PreferencesSettings />} />
            </Route>

            {/* Checkout Flow */}
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/checkout/success" element={<CheckoutSuccessPage />} />
            <Route path="/checkout/cancelled" element={<CheckoutCancelledPage />} />
            <Route path="/checkout/failed" element={<CheckoutFailedPage />} />

            {/* 404 Catch-All */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
