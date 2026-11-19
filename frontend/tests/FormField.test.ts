// @vitest-environment happy-dom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import FormField from '../app/components/FormField.vue'

const mountField = (props: Record<string, unknown>) =>
  mount(FormField, {
    props: { id: 'email', label: 'E-mail', ...props },
    slots: { default: '<template #default="{ field }"><input v-bind="field"></template>' },
    global: { stubs: { GuideIcon: true } },
  })

describe('FormField', () => {
  it('connects the label to the input', () => {
    const wrapper = mountField({})
    expect(wrapper.find('label').attributes('for')).toBe('email')
    expect(wrapper.find('input').attributes('id')).toBe('email')
  })

  it('says in words that a field is required', () => {
    expect(mountField({ required: true }).find('label').text()).toContain('(required)')
    expect(mountField({}).find('label').text()).not.toContain('(required)')
  })

  it('links the help text to the input', () => {
    const wrapper = mountField({ help: 'Never published.' })
    expect(wrapper.find('#email-help').text()).toBe('Never published.')
    expect(wrapper.find('input').attributes('aria-describedby')).toBe('email-help')
    expect(wrapper.find('input').attributes('aria-invalid')).toBeUndefined()
  })

  it('shows an error under the field and marks the input as invalid', () => {
    const wrapper = mountField({ help: 'Never published.', errors: ['Enter an address like name@example.com.'] })
    expect(wrapper.find('#email-error').text()).toContain('Enter an address like name@example.com.')
    expect(wrapper.find('input').attributes('aria-invalid')).toBe('true')
    expect(wrapper.find('input').attributes('aria-describedby')).toBe('email-help email-error')
    expect(wrapper.classes()).toContain('has-error')
  })

  it('joins several messages into one text', () => {
    const wrapper = mountField({ errors: ['Too short.', 'Too common.'] })
    expect(wrapper.find('#email-error').text()).toContain('Too short. Too common.')
  })
})
