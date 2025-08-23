/**
 * Display a list of study plans.
 *
 * @param {Object[]} plans - Array of plans returned from the API.
 * Each plan contains an id, optional due date and a list of goals
 * with at least a `title` field.
 */
export default function PlanCard({ plans = [] }) {
  return (
    <div className="card">
      <h2>Plans</h2>
      {plans.length === 0 ? (
        <p>No plans yet.</p>
      ) : (
        <ul>
          {plans.map((plan) => (
            <li key={plan.id}>
              {plan.goals.map((g) => g.title).join(', ')}
              {plan.due_date ? ` - Due ${plan.due_date}` : ''}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

