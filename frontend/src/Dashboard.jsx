import { useEffect, useState } from 'react';
import API from './api';

export default function Dashboard() {
  const [expenses, setExpenses] = useState([]);
  const [title, setTitle] = useState('');
  const [amount, setAmount] = useState('');

  const token = localStorage.getItem('token');

  const fetchExpenses = async () => {
    const res = await API.get('/expenses?token=' + token);
    setExpenses(res.data.data);
  };

  const addExpense = async () => {
    await API.post('/expenses?token=' + token, {
      title,
      amount: parseFloat(amount),
    });
    setTitle('');
    setAmount('');
    fetchExpenses();
  };

  useEffect(() => {
    fetchExpenses();
  }, []);

  return (
    <div>
      <h2>Add Expense</h2>

      <input
        placeholder='Title'
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <br /><br />

      <input
        placeholder='Amount'
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <br /><br />

      <button onClick={addExpense}>Add</button>

      <h2>Your Expenses</h2>

      {expenses.map((e) => (
        <div key={e.id}>
          {e.title} - ${e.amount}
        </div>
      ))}
    </div>
  );
}