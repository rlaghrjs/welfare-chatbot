CREATE TABLE app_installations (
	token_hash VARCHAR(64) NOT NULL,
	last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE sync_runs (
	source VARCHAR(50) NOT NULL,
	status VARCHAR(20) NOT NULL,
	checkpoint JSONB NOT NULL,
	fetched_count INTEGER NOT NULL,
	created_count INTEGER NOT NULL,
	updated_count INTEGER NOT NULL,
	failed_count INTEGER NOT NULL,
	error_summary TEXT,
	started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	finished_at TIMESTAMP WITH TIME ZONE,
	id UUID NOT NULL,
	PRIMARY KEY (id)
);

CREATE INDEX ix_sync_source_started ON sync_runs (source, started_at);

CREATE TABLE welfare_policies (
	source VARCHAR(50) NOT NULL,
	external_id VARCHAR(100) NOT NULL,
	name TEXT NOT NULL,
	summary TEXT,
	search_attributes JSONB NOT NULL,
	availability_status VARCHAR(30) NOT NULL,
	content_hash VARCHAR(64) NOT NULL,
	raw_data JSONB NOT NULL,
	first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	content_updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_policy_source_external UNIQUE (source, external_id)
);

CREATE INDEX ix_policy_availability ON welfare_policies (availability_status);

CREATE INDEX ix_policy_search_attributes ON welfare_policies USING gin (search_attributes);

CREATE TABLE profiles (
	installation_id UUID NOT NULL,
	name VARCHAR(100) NOT NULL,
	birth_date DATE,
	region VARCHAR(100),
	attributes JSONB NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(installation_id) REFERENCES app_installations (id) ON DELETE CASCADE
);

CREATE INDEX ix_profiles_installation_id ON profiles (installation_id);

CREATE TABLE welfare_policy_versions (
	policy_id UUID NOT NULL,
	sync_run_id UUID,
	version_no INTEGER NOT NULL,
	change_type VARCHAR(30) NOT NULL,
	snapshot JSONB NOT NULL,
	changes JSONB NOT NULL,
	detected_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_policy_version UNIQUE (policy_id, version_no),
	CONSTRAINT ck_version_positive CHECK (version_no > 0),
	FOREIGN KEY(policy_id) REFERENCES welfare_policies (id) ON DELETE RESTRICT,
	FOREIGN KEY(sync_run_id) REFERENCES sync_runs (id) ON DELETE SET NULL
);

CREATE INDEX ix_welfare_policy_versions_sync_run_id ON welfare_policy_versions (sync_run_id);

CREATE TABLE condition_subscriptions (
	installation_id UUID NOT NULL,
	profile_id UUID,
	name VARCHAR(100) NOT NULL,
	conditions JSONB NOT NULL,
	event_types JSONB NOT NULL,
	unknown_condition_policy VARCHAR(20) NOT NULL,
	enabled BOOLEAN NOT NULL,
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT ck_subscription_unknown CHECK (unknown_condition_policy IN ('include', 'exclude')),
	FOREIGN KEY(installation_id) REFERENCES app_installations (id) ON DELETE CASCADE,
	FOREIGN KEY(profile_id) REFERENCES profiles (id) ON DELETE RESTRICT
);

CREATE INDEX ix_condition_subscriptions_installation_id ON condition_subscriptions (installation_id);

CREATE INDEX ix_condition_subscriptions_profile_id ON condition_subscriptions (profile_id);

CREATE TABLE notifications (
	installation_id UUID NOT NULL,
	policy_version_id UUID NOT NULL,
	channel VARCHAR(20) NOT NULL,
	title TEXT NOT NULL,
	body TEXT NOT NULL,
	delivery_status VARCHAR(20) NOT NULL,
	attempt_count INTEGER NOT NULL,
	next_attempt_at TIMESTAMP WITH TIME ZONE,
	sent_at TIMESTAMP WITH TIME ZONE,
	read_at TIMESTAMP WITH TIME ZONE,
	id UUID NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_notification_delivery UNIQUE (installation_id, policy_version_id, channel),
	FOREIGN KEY(installation_id) REFERENCES app_installations (id) ON DELETE CASCADE,
	FOREIGN KEY(policy_version_id) REFERENCES welfare_policy_versions (id) ON DELETE RESTRICT
);

CREATE INDEX ix_notification_retry ON notifications (delivery_status, next_attempt_at);

CREATE INDEX ix_notification_unread ON notifications (installation_id, read_at);

CREATE INDEX ix_notifications_policy_version_id ON notifications (policy_version_id);

CREATE TABLE policy_eligibility_rules (
	policy_version_id UUID NOT NULL,
	field VARCHAR(50) NOT NULL,
	operator VARCHAR(30) NOT NULL,
	value JSONB NOT NULL,
	evidence TEXT NOT NULL,
	verification_status VARCHAR(20) NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(policy_version_id) REFERENCES welfare_policy_versions (id) ON DELETE CASCADE
);

CREATE INDEX ix_policy_eligibility_rules_policy_version_id ON policy_eligibility_rules (policy_version_id);

CREATE TABLE chat_search_results (
	message_id UUID NOT NULL,
	policy_version_id UUID NOT NULL,
	rank INTEGER NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_chat_result_version UNIQUE (message_id, policy_version_id),
	CONSTRAINT ck_result_rank CHECK (rank > 0),
	FOREIGN KEY(message_id) REFERENCES chat_messages (id) ON DELETE CASCADE,
	FOREIGN KEY(policy_version_id) REFERENCES welfare_policy_versions (id) ON DELETE RESTRICT
);

CREATE INDEX ix_chat_search_results_policy_version_id ON chat_search_results (policy_version_id);

CREATE TABLE notification_matches (
	notification_id UUID NOT NULL,
	subscription_id UUID,
	conditions_snapshot JSONB NOT NULL,
	match_reason JSONB NOT NULL,
	id UUID NOT NULL,
	PRIMARY KEY (id),
	CONSTRAINT uq_notification_match UNIQUE (notification_id, subscription_id),
	FOREIGN KEY(notification_id) REFERENCES notifications (id) ON DELETE CASCADE,
	FOREIGN KEY(subscription_id) REFERENCES condition_subscriptions (id) ON DELETE SET NULL
);

CREATE INDEX ix_notification_matches_subscription_id ON notification_matches (subscription_id);
