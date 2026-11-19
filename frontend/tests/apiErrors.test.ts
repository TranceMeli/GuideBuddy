import { describe, expect, it } from 'vitest'
import { apiErrorCode, apiErrorMessages, apiFieldErrors } from '../app/composables/useApi'

const failure = (data: unknown, statusCode = 400) => ({ data, statusCode })

describe('apiErrorMessages', () => {
  it('says so when the server cannot be reached', () => {
    expect(apiErrorMessages(new Error('network'))).toEqual(['The server cannot be reached.'])
  })

  it('asks to wait after too many requests', () => {
    expect(apiErrorMessages(failure({}, 429))[0]).toContain('Too many attempts')
  })

  it('reads a plain detail message', () => {
    expect(apiErrorMessages(failure({ detail: 'Not allowed.' }))).toEqual(['Not allowed.'])
  })

  it('puts the field label in front of a field error', () => {
    expect(apiErrorMessages(failure({ title: ['This field may not be blank.'] }))).toEqual(['Title: This field may not be blank.'])
  })

  it('never returns an empty list', () => {
    expect(apiErrorMessages(failure({ code: 'x' }))).toEqual(['An unknown error occurred.'])
  })
})

describe('apiFieldErrors', () => {
  const fields = ['username', 'email', 'password']

  it('takes the listed fields out, one list of messages each', () => {
    const split = apiFieldErrors(failure({ email: ['Enter a valid email address.'], password: ['Too short.', 'Too common.'] }), fields)
    expect(split.fields).toEqual({ email: ['Enter a valid email address.'], password: ['Too short.', 'Too common.'] })
    expect(split.other).toEqual([])
  })

  it('keeps everything else as general messages', () => {
    const split = apiFieldErrors(failure({ email: ['Taken.'], detail: 'Registration is closed.' }), fields)
    expect(split.fields).toEqual({ email: ['Taken.'] })
    expect(split.other).toEqual(['Registration is closed.'])
  })

  it('accepts a single message as text', () => {
    expect(apiFieldErrors(failure({ username: 'Already used.' }), fields).fields).toEqual({ username: ['Already used.'] })
  })

  it('falls back to the general messages when no listed field is in the answer', () => {
    const split = apiFieldErrors(failure({ detail: 'Nope.' }), fields)
    expect(split.fields).toEqual({})
    expect(split.other).toEqual(['Nope.'])
  })

  it('handles an unreachable server', () => {
    expect(apiFieldErrors(new Error('network'), fields).other).toEqual(['The server cannot be reached.'])
  })
})

describe('apiErrorCode', () => {
  it('returns the code of the response, or an empty text', () => {
    expect(apiErrorCode(failure({ code: 'email_not_verified' }))).toBe('email_not_verified')
    expect(apiErrorCode(new Error('x'))).toBe('')
  })
})
