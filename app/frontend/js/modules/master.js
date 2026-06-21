import { CodingModule } from './coding.js';
import { EvaluationModule } from './evaluation.js';
import { EventsModule } from './events.js';
import { FinancesModule } from './finances.js';
import { GymModule } from './gym.js';
import { HealthModule } from './health.js';
import { MajorEventsModule } from './major_events.js';
import { NotesModule } from './notes.js';
import { TransactionsModule } from './transactions.js';
import { AppleHealthModule } from './apple_health.js';

// The visual top-to-bottom order is dictated exactly by this list.
export const MODULE_LIST = [
    { id: "health",       module: HealthModule,      showInSafeMode: false },
    { id: "gym",          module: GymModule,         showInSafeMode: true  },
    { id: "coding",       module: CodingModule,      showInSafeMode: true  },
    { id: "finances",     module: FinancesModule,    showInSafeMode: true  },
    { id: "events",       module: EventsModule,      showInSafeMode: false },
    { id: "major_events", module: MajorEventsModule, showInSafeMode: true  },
    { id: "notes",        module: NotesModule,       showInSafeMode: false },
    { id: "evaluation",   module: EvaluationModule,  showInSafeMode: false },
    // { id: "apple_health", module: AppleHealthModule, showInSafeMode: false },
    // { id: "transactions", module: TransactionsModule, showInSafeMode: true },
];
