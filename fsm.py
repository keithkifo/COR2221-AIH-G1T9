from transitions import State
from transitions.extensions import HierarchicalMachine

class FiniteStateMachine(HierarchicalMachine):
    def __init__(self):
        super().__init__(self, states=self.init_states(), initial='waiting', ignore_invalid_triggers=True)
        self.init_main_transitions()

        # initialise sub-machine transitions to nested states
        self.init_localchat_machine()
        self.init_recommendations_machine()
    
    def init_states(self):
        states = [
            'waiting',
            {
                'name':'chat',
                'initial':'checkChat',
                'children': [
                    'checkChat',
                    'retrieveSession',
                    'ongoingSession',
                    'matchMaking',
                    'endState',
                ]
            },
            {
                'name':'reco',
                'initial':'promptUser',
                'children': [
                    'promptUser',
                    'recoSomething',
                    'recoSpecific',
                    'endState'
                ]
            }
        ]

        return states
    
    def init_main_transitions(self):
        # Transitions to sub-machines
        self.add_transitions(
            [
                ['start_chat', 'waiting','chat_checkChat'],
                ['start_reco', 'waiting','reco_promptUser']
            ]
        )
    
    def init_localchat_machine(self):
        self.add_ordered_transitions([
            'chat_checkChat',
            'chat_retrieveSession',
            'chat_ongoingSession',
            'chat_endState'
        ], loop=False)

        # Scenario: Matchmaking
        self.add_transition(trigger='chat_matchmake', source='chat_checkChat', dest='chat_matchMaking')
        self.add_transition(trigger='chat_start_session', source='chat_matchMaking', dest='chat_ongoingSession')

        # Back to main state
        self.add_transition(trigger='to_waiting', source=['chat_matchMaking','chat_endState'], dest='waiting')

    def init_recommendations_machine(self):
        self.add_ordered_transitions([
            'reco_promptUser',
            'reco_recoSomething',
            'reco_recoSpecific',
            'reco_endState',
        ], loop=False)

        # Back to main state
        self.add_transition(trigger='to_waiting', source=['reco_endState'], dest='waiting')