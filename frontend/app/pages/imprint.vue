<script setup lang="ts">
useSeoMeta({ title: 'Imprint', robots: 'noindex' })
const c = useRuntimeConfig().public
</script>

<template>
  <div>
    <h1>Imprint</h1>
    <LegalDraft />
    <h2>Information according to § 5 DDG (German Digital Services Act)</h2>
    <p>
      {{ c.operatorName || '[First and last name or company]' }}<br>
      {{ c.operatorAddress || '[Street and number, postcode and city]' }}<br>
      Germany
    </p>
    <h2>Contact</h2>
    <p>E-mail: {{ c.operatorEmail || '[E-mail address]' }}</p>
    <h2>Responsible for the content (§ 18 (2) MStV)</h2>
    <p>{{ c.operatorName || '[Name]' }}, address as above.</p>
    <h2>Community content</h2>
    <p>
      The guides are written by users. You can report unlawful content with the “Report guide”
      function on every guide page or by e-mail to the address above.
    </p>
  </div>
</template>
