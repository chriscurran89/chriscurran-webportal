library(DBI)
library(RSQLite)
con <- dbConnect(RSQLite::SQLite())

dbSendQuery(con, "SELECT * FROM GAMEMETRICS")

fresh_date <- function(){
  query <- paste0("
      SELECT
        MAX(created_at::date)
      FROM public.users")
  
  return (query)
}

condition_users <- function(condition_name=NULL) {
  if (!is.null(condition_name)){
    condition_name <- paste0("= '", condition_name,"'")
  }
  else {
    condition_name = paste0("= ANY(SELECT DISTINCT condition_name FROM medical.user_condition)")
  }
  query <- paste0("
      SELECT DISTINCT
          uc.user_id
      FROM public.users
      LEFT JOIN medical.user_condition AS uc
          ON users.user_id_hash = uc.user_id
      WHERE users.last_activity_time::date >= NOW()::date - INTERVAL '90 DAY'
      AND uc.condition_name ",condition_name)
  
  return (query)
}

tc_cohort_view <- function(tailored_community=NULL) {
  if (!is.null(tailored_community)){
    tailored_community <- paste0("= '", tailored_community,"'")
  }
  else {
    tailored_community = paste0("= ANY(SELECT DISTINCT name FROM public.tailored_communities)")
  }
  query = paste0("
      WITH
      cohort AS(
          SELECT DISTINCT
              pii.user_id
          FROM medical.pii_patient_user_data AS pii
          LEFT JOIN public.tailored_community_memberships tcm
              ON pii.plm_site_user_id = tcm.user_id
          LEFT JOIN public.tailored_communities as tc
              ON tcm.tailored_community_id = tc.id
          WHERE tc.name ",tailored_community,"),
          
      utr AS (
          SELECT DISTINCT ON (utr.user_id)
              utr.user_id,
              utr.start_date AS most_recent_thrive_report_start_date,
              utr.health_overall_rating_label AS most_recent_health_overall_rating_label,
              utr.health_change_rating_label AS most_recent_health_change_rating_label
          FROM cohort 
          LEFT JOIN medical.user_thrive_report AS utr
              USING(user_id)
          ORDER BY utr.user_id, utr.start_date DESC),
          
      feel_connected AS (
          SELECT DISTINCT ON (ute.user_id)
              ute.user_id,
              ute.start_date,
              ute.how_often_rating_label AS most_recent_connected_to_others_rating_label
          FROM cohort
          LEFT JOIN medical.user_thrive_experience AS ute
              USING(user_id)
          WHERE thrive_experience_description = 'feel connected to others'
          ORDER BY ute.user_id, ute.start_date DESC),
          
      take_charge AS (
          SELECT DISTINCT ON (ute.user_id)
              ute.user_id,
              ute.start_date,
              ute.how_often_rating_label AS most_recent_take_charge_rating_label
          FROM cohort
          LEFT JOIN medical.user_thrive_experience AS ute
              USING(user_id)
          WHERE thrive_experience_description = 'feel able to take charge of your health'
          ORDER BY ute.user_id, ute.start_date DESC),
          
      live_life AS (
          SELECT DISTINCT ON (ute.user_id)
              ute.user_id,
              ute.start_date,
              ute.how_often_rating_label AS most_recent_live_life_rating_label
          FROM cohort
          LEFT JOIN medical.user_thrive_experience AS ute
              USING(user_id)
          WHERE thrive_experience_description = 'feel able to live the life you wanted'
          ORDER BY ute.user_id, ute.start_date DESC),
          
      health_goals AS (
          SELECT DISTINCT ON (ute.user_id)
              ute.user_id,
              ute.start_date,
              ute.how_often_rating_label AS most_recent_health_goals_rating_label
          FROM cohort
          LEFT JOIN medical.user_thrive_experience AS ute
              USING(user_id)
          WHERE thrive_experience_description = 'feel you were able to stick with your health goals'
          ORDER BY ute.user_id, ute.start_date DESC),
          
      glucose AS (
          SELECT DISTINCT ON (uta.user_id)
              uta.user_id,
              uta.start_date,
              uta.how_well_rating_label AS most_recent_glucose_control_rating_label
          FROM medical.user_thrive_ability AS uta
          WHERE thrive_ability_description = 'keep your blood glucose within your target range'
          ORDER BY uta.user_id, uta.start_date DESC)
          
      SELECT
          ct.user_id,
          pu.created_at::date > NOW()::date - INTERVAL '90 DAYS' AS signedup_last90days,
          pu.last_activity_time::date > NOW()::date - INTERVAL '90 DAYS' AS active_last90days,
          pu.last_activity_time::date AS last_activity_date,
          pu.primary_condition_name,
          pu.condition_names,
          ARRAY_LENGTH(pu.condition_ids, 1) AS condition_count,
          tc.name as tc_name,
          pu.birth_year,
          pu.sex,
          pu.preferred_pronouns,
          pu.genders,
          pu.race_code,
          pu.ethnicity_code,
          utr.most_recent_health_overall_rating_label,
          utr.most_recent_health_change_rating_label,
          feel_connected.most_recent_connected_to_others_rating_label,
          take_charge.most_recent_take_charge_rating_label,
          live_life.most_recent_live_life_rating_label,
          health_goals.most_recent_health_goals_rating_label,
          glucose.most_recent_glucose_control_rating_label
      FROM cohort AS ct
      LEFT JOIN medical.patient_user AS pu
          ON ct.user_id = pu.user_id
      LEFT JOIN medical.pii_patient_user_data AS pii
          ON pu.user_id = pii.user_id
      LEFT JOIN public.tailored_community_memberships tcm
          ON pii.plm_site_user_id = tcm.user_id
      LEFT JOIN public.tailored_communities as tc
          ON tcm.tailored_community_id = tc.id
      LEFT JOIN utr
          ON pu.user_id = utr.user_id
      LEFT JOIN feel_connected
          ON pu.user_id = feel_connected.user_id
      LEFT JOIN take_charge
          ON pu.user_id = take_charge.user_id
      LEFT JOIN live_life
          ON pu.user_id = live_life.user_id
      LEFT JOIN health_goals
          ON pu.user_id = health_goals.user_id
      LEFT JOIN glucose
          ON pu.user_id = glucose.user_id")
  return (query)
}

tc_symptoms <- function(tailored_community=NULL) {
  if (!is.null(tailored_community)){
    tailored_community <- paste0("= '", tailored_community,"'")
  }
  else {
    tailored_community = paste0("= ANY(SELECT DISTINCT name FROM public.tailored_communities)")
  }
  query = paste0("
    WITH
    cohort AS(
        SELECT DISTINCT
            pii.user_id
        FROM medical.pii_patient_user_data AS pii
        LEFT JOIN public.tailored_community_memberships tcm
            ON pii.plm_site_user_id = tcm.user_id
        LEFT JOIN public.tailored_communities as tc
            ON tcm.tailored_community_id = tc.id
        WHERE tc.name ", tailored_community,")
        
    SELECT
    ct.user_id,
    ush.report_start_date::date AS report_start_date,
    ush.symptom_name,
    ush.symptom_severity_label
    FROM cohort AS ct
    LEFT JOIN medical.user_symptom_history AS ush
        USING(user_id)
    WHERE symptom_name IN(
        'depressed_mood', 'anxious_mood', 'stress', 'fatigue',
        'pain', 'feet tingling', 'feet tingling after sitting for a while',
        'fingers and feet tingling', 'nerve pain (neuralgia)',  'hands tingling',
        'sweating', 'sweating increased', 'excessive sweating', 'shakiness',
        'shakiness worsened', 'blurry vision')
    ORDER BY ush.created_at DESC")
  
  return (query)
}


tc_treatments <- function(tailored_community=NULL) {
  if (!is.null(tailored_community)){
    tailored_community <- paste0("= '", tailored_community,"'")
  }
  else {
    tailored_community = paste0("= ANY(SELECT DISTINCT name FROM public.tailored_communities)")
  }
  query = paste0("
    WITH
    cohort AS(
        SELECT DISTINCT
            pii.user_id
        FROM medical.pii_patient_user_data AS pii
        LEFT JOIN public.tailored_community_memberships tcm
            ON pii.plm_site_user_id = tcm.user_id
        LEFT JOIN public.tailored_communities as tc
            ON tcm.tailored_community_id = tc.id
        WHERE tc.name ", tailored_community,")
        
    SELECT
        ct.user_id,
        ut.overall_start_date::date AS tx_start_date,
        ut.treatment_name,
        ut.treatment_id,
        CASE
            WHEN 50=ANY(t.commonly_prescribed_for_condition_ids) THEN 't2d' ELSE 'not_t2d' END AS tx_associated_with,
        ute.evaluation_date::date AS report_start_date,
        ute.adherence_label,
        ute.burden_label,
        ute.side_effects_label,
        utee.efficacy_for_purpose_label
    FROM cohort AS ct
    LEFT JOIN medical.user_treatment AS ut
        USING(user_id)
    LEFT JOIN medical.user_treatment_evaluation AS ute
        USING(user_id, treatment_id)
    LEFT JOIN medical.treatment AS t
        USING(treatment_id)
    LEFT JOIN medical.user_treatment_efficacy_evaluation as utee
        USING(user_treatment_evaluation_id)")
  
  return (query)
}

tc_comorbs <- function(tailored_community=NULL) {
  if (!is.null(tailored_community)){
    tailored_community <- paste0("= '", tailored_community,"'")
  }
  else {
    tailored_community = paste0("= ANY(SELECT DISTINCT name FROM public.tailored_communities)")
  }
  query = paste0("
    WITH
    cohort AS(
        SELECT DISTINCT
            pii.user_id
        FROM medical.pii_patient_user_data AS pii
        LEFT JOIN public.tailored_community_memberships tcm
            ON pii.plm_site_user_id = tcm.user_id
        LEFT JOIN public.tailored_communities as tc
            ON tcm.tailored_community_id = tc.id
        WHERE tc.name ", tailored_community,")
        
    SELECT
    ut.condition_name,
    COUNT (DISTINCT cohort.user_id)
    FROM cohort
    LEFT JOIN medical.user_condition AS ut
        USING(user_id)
    GROUP BY ut.condition_name
    ORDER BY COUNT DESC")
  
  return (query)
}


query_counts_by_daterange <- function(start_date, end_date, condition_name=NULL, tailored_community=NULL) {
  if (!is.null(condition_name)){
    condition_name <- paste0("= \'", condition_name,"\'")
  }
  else {
    condition_name = paste0("= ANY(SELECT DISTINCT condition_name FROM medical.user_condition)")
  }
  if (!is.null(tailored_community)){
    tailored_community = paste0("tc.name ILIKE('",tailored_community,"')")
  }
  else {
    tailored_community = paste0("(tc.name IS NOT NULL OR tc.name IS NULL)")
  }
  query = paste0("
    WITH 
    cohort AS(
      SELECT DISTINCT
        users.id,
        users.metric_guid,
        users.user_id_hash
      FROM medical.patient_user AS pu
      LEFT JOIN public.users
        ON users.user_id_hash = pu.user_id
      LEFT JOIN medical.user_condition AS uc
        ON pu.user_id = uc.user_id
      LEFT JOIN public.tailored_community_memberships tcm
        ON users.id = tcm.user_id
      LEFT JOIN public.tailored_communities as tc
        ON tcm.tailored_community_id = tc.id
      WHERE uc.condition_name ", condition_name,"),
      
    tc_newswire AS(
      WITH 
      posts AS(
        SELECT 
        	user_id,
        	stream_event_id,
        	created_at
        FROM intermediate.newswire_stream_event
        WHERE '_PostedToTailoredCommunity:1' = ANY(tags)),
      comments AS(
        SELECT
          user_id,
          stream_event_id,
          created_at
      	 FROM intermediate.newswire_comment
        WHERE stream_event_id = ANY(SELECT DISTINCT stream_event_id FROM posts)),
      combined AS(
        SELECT 
          *
        FROM posts
        UNION
        SELECT
          *
        FROM comments)
        
      SELECT
        user_id,
        COUNT(DISTINCT created_at::date) AS tc_newswire_days
      FROM combined
      WHERE created_at::date >= '",start_date,"'
      AND created_at::date < '",end_date,"'
      GROUP BY user_id)
        
    SELECT
    cohort.id::int,
    cohort.user_id_hash,
    cohort.metric_guid,
    ARRAY_AGG(DISTINCT(tc.name)) AS tc_names,
    SUM(uda.sessions) AS session_count,
    SUM(uda.sessions_day::int) AS session_days,
    SUM(uda.session_minutes::int) AS session_minutes,
    SUM(uda.pms_sent::int) AS messages_sent_count,
    SUM(uda.pms_sent_day::int) AS messages_sent_days,
    SUM(uda.pms_received::int) AS messages_received_count,
    SUM(uda.pms_received_day::int) AS messages_received_days,
    SUM(uda.forum_posts::int) AS forum_post_count,
    SUM(uda.forum_posts_day::int) AS forum_post_days,
    SUM(uda.forum_topic_list_views::int) AS forum_topic_views_count,
    SUM(uda.forum_topic_list_views_day::int) AS forum_topic_view_days,
    SUM(uda.feed_comments_given::int) AS feed_comments_given_count,
    SUM(uda.feed_comments_given_day::int) AS feed_comment_given_days,
    SUM(uda.feed_comments_received::int) AS feed_comments_received_count,
    SUM(uda.feed_comments_received_day::int) AS feed_comment_received_days,
    SUM(uda.feed_follows::int) AS feed_follows_count,
    SUM(uda.feed_follows_day::int) AS feed_follow_days,
    SUM(uda.feed_likes_given::int) AS feed_likes_given_count,
    SUM(uda.feed_likes_given_day::int) AS feed_likes_given_days,
    SUM(uda.feed_likes_given::int) AS feed_likes_given_count,
    SUM(uda.feed_likes_given_day::int) AS feed_likes_given_days,
    SUM(uda.feed_likes_received::int) AS feed_likes_received_count,
    SUM(uda.feed_likes_received_day::int) AS feed_likes_received_days,
    SUM(uda.symptom_reports::int) AS symptom_reports_count,
    SUM(uda.symptom_reports_day::int) AS symptom_reports_days,
    SUM(uda.treatment_evaluations::int) AS treatment_eval_count,
    SUM(uda.treatment_evaluations_day::int) AS treatment_eval_days,
    SUM(uda.instant_mes_day::int) AS dailyMe_days,
    COALESCE(tc_newswire_days,0) AS tc_newswire_days,
    CONCAT('",start_date,"') AS week
    FROM cohort
    LEFT JOIN activity.user_daily_activity AS uda
      ON cohort.user_id_hash = uda.user_id
    LEFT JOIN tc_newswire AS nw
      ON cohort.id = nw.user_id
    LEFT JOIN public.tailored_community_memberships tcm
      ON cohort.id = tcm.user_id
    LEFT JOIN public.tailored_communities as tc
      ON tcm.tailored_community_id = tc.id
    WHERE calendar_date >= '",start_date,"'
    AND calendar_date < '",end_date,"'
    AND ",tailored_community,"
    GROUP BY cohort.id,cohort.user_id_hash,cohort.metric_guid,tc_newswire_days")
  
  return (query)
}

p2p_interaction <- function(tailored_community=NULL, start_date, end_date) {
  if (!is.null(tailored_community)){
    tailored_community <- paste0("= '", tailored_community,"'")
  }
  else {
    tailored_community = paste0("= ANY(SELECT DISTINCT name FROM public.tailored_communities)")
  }
  query <- paste0("
      WITH
      cohort AS(
        SELECT DISTINCT
            pii.user_id
        FROM medical.pii_patient_user_data AS pii
        LEFT JOIN public.tailored_community_memberships tcm
            ON pii.plm_site_user_id = tcm.user_id
        LEFT JOIN public.tailored_communities as tc
            ON tcm.tailored_community_id = tc.id
        WHERE tc.name ", tailored_community,"),
      
      mess AS(
        SELECT 
          COUNT(DISTINCT uda.user_id) AS unique_messaging_users,
          SUM(uda.pms_sent) AS total_messages_count,
          COALESCE('",start_date,"','",start_date,"')::date AS week_of
        FROM cohort
        INNER JOIN activity.user_daily_activity AS uda
         ON cohort.user_id = uda.user_id
        WHERE uda.pms_sent > 0
        AND calendar_date >= '",start_date,"'
        AND calendar_date < '",end_date,"'),
        
      feed AS(
        SELECT
          COUNT(DISTINCT uda.user_id) AS unique_following_users,
          SUM(uda.feed_follows) AS total_follows_count,
          COALESCE('",start_date,"','",start_date,"')::date AS week_of
        FROM cohort
        INNER JOIN activity.user_daily_activity AS uda
         ON cohort.user_id = uda.user_id
        WHERE uda.feed_follows > 0
        AND calendar_date >= '",start_date,"'
        AND calendar_date < '",end_date,"')
        
      SELECT
        *
      FROM mess
      JOIN feed
        USING(week_of)")
  
  return (query)
}
