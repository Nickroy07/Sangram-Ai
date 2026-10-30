import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { battlesApi, savedApi, subscribeBattle } from '../../services/api'
import { useToast } from '../../context/ToastContext'
import { Button } from '../../components/common/Button'

export const ArenaViewPage = () => {
  const { id } = useParams()
  const { showToast } = useToast()
  const [battle, setBattle] = useState(null)
  const [error, setError] = useState('')
  const [round, setRound] = useState(1)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    let active = true
    let closeStream = () => {}
    const load = async () => {
      try {
        const initial = await battlesApi.get(id)
        if (!active) return
        setBattle({ ...initial, messages: [], roundSummaries: [] })
        if (initial.status === 'failed') { setError(initial.finalAnswer || 'The battle failed.'); return }
        if (initial.status === 'completed') { setBattle(initial); return }
        let currentRound = 1
        closeStream = subscribeBattle(id, (type, data) => {
          if (!active) return
          if (type === 'battle.stage') { currentRound = data.round; setRound(data.round); return }
          if (type === 'battle.message.start') {
            const fighter = initial.fighters.find((item) => item.modelId === data.modelId)
            setBattle((value) => ({ ...value, messages: [...value.messages, {
              id: data.messageId, round: currentRound, stageKey: '', stageLabel: data.stageLabel,
              speaker: data.speaker, modelId: data.modelId, modelName: fighter?.name || data.modelId,
              provider: fighter?.provider || '', modelLabel: fighter?.modelLabel || '', text: '', challenges: null,
            }] }))
            return
          }
          if (type === 'battle.message.chunk') {
            setBattle((value) => ({ ...value, messages: value.messages.map((message) => message.id === data.messageId ? { ...message, text: message.text + data.delta } : message) }))
            return
          }
          if (type === 'battle.message.done') {
            setBattle((value) => ({ ...value, messages: value.messages.map((message) => message.id === data.messageId ? { ...message, challenges: data.challenges, contention: data.contention, converging: data.converging } : message) }))
            return
          }
          if (type === 'battle.round.summary') { setBattle((value) => ({ ...value, roundSummaries: [...value.roundSummaries, data.summary] })); return }
          if (type === 'battle.final') { setBattle((value) => ({ ...value, finalAnswer: data.finalAnswer, insights: data.insights, agreement: data.agreement })); return }
          if (type === 'battle.error') { setError(data.message || 'The battle failed.'); closeStream(); return }
          if (type === 'battle.done') { setBattle((value) => ({ ...value, status: 'completed' })); closeStream() }
        }, (err) => { if (active) setError(err.message) })
      } catch (err) { if (active) setError(err.message) }
    }
    load()
    return () => { active = false; closeStream() }
  }, [id])

  const saveToLibrary = async () => {
    try {
      await savedApi.save({
        battleId: battle.id, question: battle.question, finalAnswer: battle.finalAnswer,
        fighters: battle.fighters.map((fighter) => fighter.modelId)
      })
      setSaved(true)
      showToast('Saved to your account.', 'success')
    } catch (err) { showToast(err.message, 'error') }
  }

  if (error) return <div className="arena-loading-screen py-16 text-center"><p className="auth-alert error-alert">{error}</p><Link to="/app/arena"><Button variant="primary">Start another battle</Button></Link></div>
  if (!battle) return <div className="arena-loading-screen py-16 text-center"><div className="btn-spinner mx-auto mb-4" /><p className="text-muted">Connecting to the battle…</p></div>

  const visibleMessages = battle.messages.filter((message) => message.round === round)
  return <div className="war-room-view">
    <div className="war-room-header-bar">
      <div className="header-bar-left"><div className="status-indicator-pill"><span className="live-dot" /><span>COMPLETED</span></div><h1 className="war-room-heading">{battle.question}</h1></div>
      <Link to="/app/arena"><Button variant="primary" size="sm">New Battle</Button></Link>
    </div>
      {battle.status !== 'completed' && <p className="text-muted">Generating with the selected providers…</p>}
      <nav className="stage-nav-pillbox" aria-label="Battle rounds">
      {['Opening', 'Counterarguments', 'Rebuttals', 'Final Positions'].map((label, index) => <button key={label} type="button" className={`stage-step-btn ${round === index + 1 ? 'active' : ''}`} onClick={() => setRound(index + 1)}>{index + 1}. {label}</button>)}
    </nav>
    <div className="war-room-content-grid mt-6">
      <section className="debate-stream-column"><div className="column-title-bar"><h3 className="column-title">Round {round} · {visibleMessages.length} responses</h3></div>
        <div className="debate-rounds-stack">{visibleMessages.map((message) => <article key={message.id} className="debate-round-box"><div className="round-box-header"><div className="speaker-identity"><span className="speaker-name">{message.modelName}</span><span className="speaker-role-tag">{message.provider} · {message.stageLabel}</span></div></div><p className="round-speech-text">{message.text}</p>{message.challenges && <p className="text-muted">Responding to: {message.challenges}</p>}</article>)}</div>
      </section>
      <aside className="synthesis-column"><div className="synthesis-verdict-card"><div className="verdict-card-top"><span className="verdict-tag">CONSOLIDATED SYNTHESIS</span></div><h3 className="verdict-card-title">Recommendation</h3><div className="verdict-text-box"><p>{battle.finalAnswer}</p></div><p className="text-muted">Agreement score: {battle.agreement?.score ?? 'Not calculated'}{battle.agreement?.note ? ` · ${battle.agreement.note}` : ''}</p><div className="verdict-actions-row"><Button variant="primary" className="w-full" onClick={saveToLibrary} disabled={saved}>{saved ? 'Saved' : 'Save to Library'}</Button><Button variant="outline" className="w-full mt-2" onClick={() => navigator.clipboard?.writeText(battle.finalAnswer)}>Copy recommendation</Button></div></div></aside>
    </div>
  </div>
}
