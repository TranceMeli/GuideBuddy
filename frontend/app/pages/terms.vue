<script setup lang="ts">
useSeoMeta({ title: 'Terms of use', robots: 'noindex' })
</script>

<template>
  <div>
    <h1>Terms of use</h1>
    <LegalDraft />
    <h2>1. Scope</h2>
    <p>These terms apply to the use of GuideBuddy. You can read without an account; you need an account to write.</p>
    <h2>2. Account</h2>
    <p>You need a valid e-mail address, which you must confirm. Keep your password secret. New accounts can only edit guides after a waiting period.</p>
    <h2>3. Your contributions</h2>
    <ul>
      <li>You may only publish content that you wrote yourself or are allowed to use.</li>
      <li>You publish your contributions under <NuxtLink to="/license">CC BY-SA 4.0</NuxtLink>.</li>
      <li>Your user name is shown publicly in the edit history.</li>
    </ul>
    <h2>4. Prohibited content</h2>
    <p>Spam, advertising, insults, unlawful content, copyright infringements and instructions that seriously endanger others are not allowed.</p>
    <h2>5. Moderation</h2>
    <p>Moderators may revert or lock guides and ban accounts for violations. Content can be reported with “Report guide”.</p>
    <h2>6. Liability</h2>
    <p>The guides come from the community. No guarantee is given that they are correct or complete; you follow instructions at your own risk.</p>
    <h2>7. Termination</h2>
    <p>You can delete your account at any time under “Account”. Accounts may be banned for serious violations.</p>
  </div>
</template>
