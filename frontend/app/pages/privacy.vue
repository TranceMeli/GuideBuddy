<script setup lang="ts">
useSeoMeta({ title: 'Privacy policy', robots: 'noindex' })
const c = useRuntimeConfig().public
</script>

<template>
  <div>
    <h1>Privacy policy</h1>
    <LegalDraft />
    <h2>Controller</h2>
    <p>
      {{ c.operatorName || '[Name]' }}, {{ c.operatorAddress || '[Address]' }},
      e-mail: {{ c.operatorEmail || '[E-mail]' }}
    </p>

    <h2>What data we process</h2>
    <ul>
      <li>
        <strong>Visiting the site:</strong> for technical reasons the server processes your IP address
        and request data (for example in server logs). We also use the IP address for a short time to
        limit abuse (spam, password guessing). Legal basis: Art. 6 (1) (f) GDPR.
      </li>
      <li>
        <strong>Account:</strong> user name, e-mail address, password (only as a hash), and when you
        confirmed your account and accepted the terms. Legal basis: Art. 6 (1) (b) GDPR.
      </li>
      <li>
        <strong>Contributions:</strong> guides and their edit history with your user name are public.
        Legal basis: Art. 6 (1) (b) GDPR.
      </li>
      <li>
        <strong>Reports:</strong> only moderators can see who reported what.
      </li>
      <li>
        <strong>“Did this help?”:</strong> the answers are counted without an account or a link to you.
      </li>
    </ul>

    <h2>Cookies</h2>
    <p>
      We set two technically necessary cookies (“gb_access” and “gb_refresh”) that keep you signed in.
      JavaScript cannot read them (HttpOnly); the first is valid for a few minutes and is renewed
      automatically, the second expires after 14 days. Two more cookies remember your display choices
      for one year: “gb_theme” (light or dark mode) and “gb_fs” (text size). There are no tracking
      or advertising cookies.
    </p>

    <h2>Service providers</h2>
    <ul>
      <li>Hosting: {{ c.hostingProvider || '[Hosting provider]' }}</li>
      <li>E-mail delivery: {{ c.mailProvider || '[E-mail provider]' }}</li>
      <li v-if="c.turnstileSiteKey">
        Captcha: Cloudflare Turnstile (a script from Cloudflare is loaded for this when you register).
      </li>
    </ul>

    <h2>Storage period</h2>
    <p>
      Unconfirmed accounts are deleted after a few days. When you delete your account, your user name,
      e-mail address and sign-in data are removed; your contributions stay without a link to you.
      Server logs: [enter period].
    </p>

    <h2>Your rights</h2>
    <p>
      You have the right of access, rectification, erasure, restriction, data portability and objection,
      and the right to lodge a complaint with a data protection supervisory authority. Write to us at
      {{ c.operatorEmail || '[E-mail]' }}.
    </p>
  </div>
</template>
