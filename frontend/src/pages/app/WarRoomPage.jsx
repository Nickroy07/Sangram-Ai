import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { battlesApi } from '../../services/api'
import { Button } from '../../components/common/Button'

export const WarRoomPage = () => {
  const [battles, setBattles] = useState([])
  const [error, setError] = useState('')
  useEffect(() => { battlesApi.history(1, 20).then((page) => setBattles(page.items || [])).catch((e) => setError(e.message)) }, [])
  return <section className="war-room-view">
    <div className="page-header-row"><div><h1 className="page-title">War Room</h1><p className="page-sub">Review live and completed battles from your account.</p></div><Link to="/app/arena/new"><Button variant="primary">Start a battle</Button></Link></div>
    {error && <p className="auth-alert error-alert mt-6" role="alert">{error}</p>}
    <div className="clean-card-box mt-6"><h2 className="box-title">Your battles</h2>
      {battles.length ? <div className="breakdown-clean-list mt-4">{battles.map((battle) => <article className="breakdown-clean-row" key={battle.id}><div><strong>{battle.title || battle.question}</strong><p className="text-muted">{battle.status} · {new Date(battle.date || battle.createdAt || Date.now()).toLocaleString()}</p></div><Link to={`/app/arena/${battle.id}`}><Button variant="outline" size="sm">Open battle</Button></Link></article>)}</div> : !error && <p className="text-muted mt-4">No battles yet. Start one to see model responses here.</p>}
    </div>
  </section>
}
